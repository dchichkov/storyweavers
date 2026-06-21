#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/discourage_slay_conflict_transformation_fable.py
============================================================================

A standalone storyworld for a small fable domain: a proud young animal sees a
frightening shape at dusk, wants to slay it, and a wiser companion tries to
discourage that rash choice. The central conflict is between hot pride and calm
attention. The transformation is both in the world and in the hero: poor light
turns an ordinary thing into a seeming beast, and clearer light turns fear and
boasting into understanding.

Run it
------
    python storyworlds/worlds/gpt-5.4/discourage_slay_conflict_transformation_fable.py
    python storyworlds/worlds/gpt-5.4/discourage_slay_conflict_transformation_fable.py --place vineyard --apparition vine_arch
    python storyworlds/worlds/gpt-5.4/discourage_slay_conflict_transformation_fable.py --apparition stone_post
    python storyworlds/worlds/gpt-5.4/discourage_slay_conflict_transformation_fable.py --all
    python storyworlds/worlds/gpt-5.4/discourage_slay_conflict_transformation_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/discourage_slay_conflict_transformation_fable.py --verify
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
        female = {"hen", "goose", "ewe", "vixen"}
        male = {"rooster", "ram", "fox", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    id: str
    label: str
    path: str
    affordances: set[str] = field(default_factory=set)
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
class Apparition:
    id: str
    seeming: str
    actual: str
    look_line: str
    truth_line: str
    confusion: int
    tangly: bool = False
    noisy: bool = False
    misreadable: bool = True
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
class Reveal:
    id: str
    label: str
    clarity: int
    place_ok: set[str] = field(default_factory=set)
    approach: str = ""
    ending: str = ""
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
class AnimalRole:
    species: str
    title: str
    traits: list[str] = field(default_factory=list)
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
class StoryParams:
    place: str
    apparition: str
    reveal: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    helper_status: str
    hero_trait: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "place": place,
            "hero_id": "",
            "helper_id": "",
            "apparition_id": "",
            "reveal_id": "",
        }

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


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    app = world.get(world.facts["apparition_id"])
    hero = world.get(world.facts["hero_id"])
    if app.meters["struck"] < THRESHOLD or not app.attrs.get("tangly"):
        return out
    sig = ("tangle", app.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["stuck"] += 1
    hero.memes["fear"] += 1
    hero.memes["shame"] += 1
    out.append("__tangle__")
    return out


def _r_fluster(world: World) -> list[str]:
    out: list[str] = []
    app = world.get(world.facts["apparition_id"])
    hero = world.get(world.facts["hero_id"])
    if app.meters["struck"] < THRESHOLD or app.attrs.get("tangly"):
        return out
    sig = ("fluster", app.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["shame"] += 1
    out.append("__fluster__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    app = world.get(world.facts["apparition_id"])
    hero = world.get(world.facts["hero_id"])
    helper = world.get(world.facts["helper_id"])
    if app.meters["lit"] < THRESHOLD:
        return out
    sig = ("reveal", app.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    app.meters["revealed"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["wisdom"] += 1
    hero.memes["pride"] = max(0.0, hero.memes["pride"] - 1.0)
    helper.memes["care"] += 1
    out.append("__revealed__")
    return out


CAUSAL_RULES = [
    Rule(name="tangle", tag="physical", apply=_r_tangle),
    Rule(name="fluster", tag="physical", apply=_r_fluster),
    Rule(name="reveal", tag="understanding", apply=_r_reveal),
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


PLACES = {
    "vineyard": Place(
        id="vineyard",
        label="the vineyard",
        path="between the grape rows",
        affordances={"vine_arch"},
        tags={"vineyard"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        path="near the wash line",
        affordances={"laundry_sheet", "stone_post"},
        tags={"courtyard"},
    ),
    "riverbank": Place(
        id="riverbank",
        label="the riverbank",
        path="beside the reeds",
        affordances={"reed_clump"},
        tags={"riverbank"},
    ),
}

APPARITIONS = {
    "vine_arch": Apparition(
        id="vine_arch",
        seeming="a crouching dragon",
        actual="a bent arch of old grapevine",
        look_line="The twisted vines made a horned shadow across the path.",
        truth_line="In clearer light, the dragon became only an old vine arch with leaves hanging from it.",
        confusion=3,
        tangly=True,
        noisy=False,
        misreadable=True,
        tags={"shadow", "vines"},
    ),
    "laundry_sheet": Apparition(
        id="laundry_sheet",
        seeming="a pale ghost",
        actual="a bedsheet on the wash line",
        look_line="The loose cloth billowed and bowed as if it were breathing.",
        truth_line="In clearer light, the ghost became only a clean bedsheet dancing on the line.",
        confusion=2,
        tangly=True,
        noisy=False,
        misreadable=True,
        tags={"shadow", "laundry"},
    ),
    "reed_clump": Apparition(
        id="reed_clump",
        seeming="a hissing serpent",
        actual="a clump of river reeds",
        look_line="The reeds bowed together and whispered in the wind like scales rubbing.",
        truth_line="In clearer light, the serpent became only a clump of reeds with the river moving behind it.",
        confusion=3,
        tangly=True,
        noisy=True,
        misreadable=True,
        tags={"reeds", "wind"},
    ),
    "stone_post": Apparition(
        id="stone_post",
        seeming="a giant",
        actual="a square old stone post",
        look_line="The post stood still and plain on the edge of the yard.",
        truth_line="It was a stone post all along.",
        confusion=1,
        tangly=False,
        noisy=False,
        misreadable=False,
        tags={"stone"},
    ),
}

REVEALS = {
    "lantern": Reveal(
        id="lantern",
        label="a lantern",
        clarity=3,
        place_ok={"vineyard", "courtyard", "riverbank"},
        approach="lifted a small lantern and let its steady light fall across the shape",
        ending="The lantern painted warm gold on the path, and the fear melted out of the evening.",
        tags={"light", "lantern"},
    ),
    "sunrise": Reveal(
        id="sunrise",
        label="the sunrise",
        clarity=3,
        place_ok={"vineyard", "courtyard", "riverbank"},
        approach="waited together until the sunrise spread milk-pale light over everything",
        ending="When morning touched the world, nothing needed fighting anymore.",
        tags={"light", "sunrise"},
    ),
    "closer_look": Reveal(
        id="closer_look",
        label="a closer look",
        clarity=2,
        place_ok={"courtyard"},
        approach="walked near with slow steps and looked from three paces away instead of from the dark gate",
        ending="Nearness did what boasting could not: it made the truth plain.",
        tags={"attention"},
    ),
}

HERO_NAMES = {
    "goat": ["Pip", "Nim", "Tup", "Bram"],
    "fox": ["Rill", "Moss", "Flint", "Vix"],
    "rooster": ["Red", "Cob", "Brisk", "Proudwing"],
}

HELPER_NAMES = {
    "elder": {
        "tortoise": ["Moss", "Old Shell", "Tansy"],
        "owl": ["Hollow", "Ashfeather", "Elder Moon"],
    },
    "peer": {
        "lamb": ["Mallow", "Softstep", "Pale"],
        "duck": ["Pebble", "Drift", "Ripple"],
    },
}

HERO_TRAITS = ["rash", "vain", "bold", "careful", "thoughtful", "humble"]
WISE_TRAITS = {"careful", "thoughtful", "humble"}
PRIDE_LEVEL = {
    "rash": 6,
    "vain": 6,
    "bold": 5,
    "careful": 2,
    "thoughtful": 3,
    "humble": 2,
}
HELPER_POWER = {"elder": 3, "peer": 1}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for apparition_id in sorted(place.affordances):
            apparition = APPARITIONS[apparition_id]
            if not apparition.misreadable:
                continue
            for reveal_id, reveal in REVEALS.items():
                if reveal_works(place, apparition, reveal):
                    combos.append((place_id, apparition_id, reveal_id))
    return sorted(combos)


def reveal_works(place: Place, apparition: Apparition, reveal: Reveal) -> bool:
    return (
        apparition.misreadable
        and place.id in reveal.place_ok
        and reveal.clarity >= apparition.confusion
    )


def explain_rejection(place: Place, apparition: Apparition, reveal: Optional[Reveal]) -> str:
    if apparition.id not in place.affordances:
        return (
            f"(No story: {apparition.actual} does not belong in {place.label}, so the fable's problem does not arise there.)"
        )
    if not apparition.misreadable:
        return (
            f"(No story: {apparition.actual} is too plain to be mistaken for a beast, so there is no honest conflict to resolve.)"
        )
    if reveal is not None and not reveal_works(place, apparition, reveal):
        return (
            f"(No story: {reveal.label} is not strong enough to make {apparition.actual} plain in that setting. Pick a clearer reveal.)"
        )
    return "(No story: this combination does not make a reasonable fable.)"


def would_heed(hero_trait: str, helper_status: str) -> bool:
    return PRIDE_LEVEL[hero_trait] <= HELPER_POWER[helper_status] + 2


def outcome_of(params: StoryParams) -> str:
    return "heeded" if would_heed(params.hero_trait, params.helper_status) else "lunged"


def introduce(world: World, hero: Entity, helper: Entity, apparition: Apparition) -> None:
    world.say(
        f"At dusk in {world.place.label}, {hero.id} the young {hero.type} walked {world.place.path} with {helper.id}, "
        f"a {helper.attrs['status']} {helper.type} whose steps were slow and sure."
    )
    world.say(
        f"{apparition.look_line} To {hero.id}'s quick eyes it looked like {apparition.seeming}."
    )


def boast(world: World, hero: Entity, apparition: Apparition) -> None:
    hero.memes["fear"] += 1
    hero.memes["pride"] += float(PRIDE_LEVEL[hero.attrs["trait"]])
    world.say(
        f'"Stand back," cried {hero.id}. "I will slay {apparition.seeming} before it troubles the path!"'
    )


def warning(world: World, helper: Entity, hero: Entity, apparition: Apparition) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} raised one calm foot and tried to discourage him. '
        f'"Dusk is a tailor of false shapes," {helper.pronoun()} said. '
        f'"Look twice before you strike once. A thing that seems like {apparition.seeming} may be less than it appears."'
    )


def lower_weapon(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["restraint"] += 1
    hero.memes["respect"] += 1
    world.say(
        f"{hero.id} still trembled, but {hero.pronoun()} lowered the stick and listened."
    )
    world.say(
        f"In that small pause, the night grew less fierce and {helper.id}'s steady voice grew larger."
    )


def lunge(world: World, hero: Entity, apparition_ent: Entity, apparition: Apparition) -> None:
    apparition_ent.meters["struck"] += 1
    hero.memes["defiance"] += 1
    propagate(world, narrate=False)
    if apparition.tangly:
        if apparition.id == "laundry_sheet":
            world.say(
                f'{hero.id} would not listen. "{hero.pronoun().capitalize()} who hesitates feeds monsters," {hero.pronoun()} said, and {hero.pronoun()} sprang forward. '
                f"The cloth wrapped around {hero.pronoun('possessive')} face and shoulders at once."
            )
        else:
            world.say(
                f'{hero.id} would not listen. "{hero.pronoun().capitalize()} who hesitates feeds monsters," {hero.pronoun()} said, and {hero.pronoun()} sprang forward. '
                f"{hero.pronoun('possessive').capitalize()} feet slid, and the shape caught at {hero.pronoun('possessive')} legs and horns."
            )
    else:
        world.say(
            f'{hero.id} would not listen. "{hero.pronoun().capitalize()} who hesitates feeds monsters," {hero.pronoun()} said, and {hero.pronoun()} struck at the shape. '
            f"The blow rang back at {hero.pronoun('object')} and made {hero.pronoun('object')} jump."
        )


def consequence(world: World, hero: Entity, apparition: Apparition) -> None:
    if hero.meters["stuck"] >= THRESHOLD:
        world.say(
            f"{hero.id} kicked and twisted, but the more {hero.pronoun()} fought, the more foolish and frightened {hero.pronoun()} felt."
        )
    else:
        world.say(
            f"The sound of the blow answered with emptiness, and {hero.id} felt shame rise hotter than courage."
        )
    if apparition.noisy:
        world.say("All the while, the reeds kept whispering their thin river-song, which was less a hiss than a wind-bent rattle.")


def reveal_truth(world: World, helper: Entity, hero: Entity, apparition_ent: Entity, apparition: Apparition, reveal: Reveal) -> None:
    apparition_ent.meters["lit"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} {reveal.approach}. {apparition.truth_line}"
    )
    if hero.meters["stuck"] >= THRESHOLD:
        world.say(
            f"{helper.id} gently freed {hero.id}, and {hero.id} stood very still, wishing the earth were softer beneath {hero.pronoun('possessive')} feet."
        )
    else:
        world.say(
            f"{hero.id} blinked hard. Now that the truth had a shape, {hero.pronoun('possessive')} brave speech sounded small to {hero.pronoun('object')}."
        )
    world.say(reveal.ending)


def transformed_end(world: World, hero: Entity, helper: Entity, apparition: Apparition) -> None:
    hero.memes["wisdom"] += 1
    world.say(
        f'"I came to slay {apparition.seeming}," said {hero.id}, "and nearly made war on {apparition.actual}."'
    )
    world.say(
        f'{helper.id} nodded. "A proud heart turns shadows into enemies. A patient heart turns enemies back into shadows."'
    )
    world.say(
        f"From then on, when a shape startled {hero.id}, {hero.pronoun()} first looked for its true name before reaching for a stick."
    )


def tell(
    place: Place,
    apparition: Apparition,
    reveal: Reveal,
    hero_name: str,
    hero_type: str,
    helper_name: str,
    helper_type: str,
    helper_status: str,
    hero_trait: str,
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            role="hero",
            traits=[hero_trait],
            attrs={"trait": hero_trait},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            traits=["calm", "watchful"],
            attrs={"status": helper_status},
        )
    )
    apparition_ent = world.add(
        Entity(
            id="apparition",
            kind="thing",
            type="apparition",
            label=apparition.actual,
            attrs={
                "seeming": apparition.seeming,
                "actual": apparition.actual,
                "tangly": apparition.tangly,
                "noisy": apparition.noisy,
            },
        )
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        apparition_cfg=apparition,
        reveal_cfg=reveal,
        apparition=apparition_ent,
        place=place,
        hero_id=hero.id,
        helper_id=helper.id,
        apparition_id=apparition_ent.id,
        reveal_id=reveal.id,
        conflict="",
        outcome="",
    )

    introduce(world, hero, helper, apparition)

    world.para()
    boast(world, hero, apparition)
    warning(world, helper, hero, apparition)

    if would_heed(hero_trait, helper_status):
        world.facts["conflict"] = "restraint"
        lower_weapon(world, hero, helper)
        world.para()
        reveal_truth(world, helper, hero, apparition_ent, apparition, reveal)
        transformed_end(world, hero, helper, apparition)
        world.facts["outcome"] = "heeded"
    else:
        world.facts["conflict"] = "attack"
        lunge(world, hero, apparition_ent, apparition)
        consequence(world, hero, apparition)
        world.para()
        reveal_truth(world, helper, hero, apparition_ent, apparition, reveal)
        transformed_end(world, hero, helper, apparition)
        world.facts["outcome"] = "lunged"

    return world


KNOWLEDGE = {
    "shadow": [
        (
            "Why can shadows look frightening at dusk?",
            "At dusk the light is weak and stretched out, so ordinary things can throw big crooked shapes. Your eyes can guess wrong before your mind has time to check."
        )
    ],
    "light": [
        (
            "Why does a lantern help you see the truth?",
            "A lantern throws steady light on the whole shape instead of only the dark edge. That makes the real object easier to recognize."
        )
    ],
    "sunrise": [
        (
            "Why do things look different at sunrise than at dusk?",
            "Morning light fills in more color and detail. When you can see more clearly, scary guesses often turn back into ordinary things."
        )
    ],
    "attention": [
        (
            "Why is looking closely better than guessing?",
            "Looking closely gives you more facts. Guessing too fast can make you afraid of something harmless."
        )
    ],
    "vines": [
        (
            "Why can vines tangle around an animal?",
            "Vines bend and catch on legs or horns when someone pushes into them. The harder you thrash, the tighter they can seem."
        )
    ],
    "laundry": [
        (
            "Why does a sheet move like a ghost in the wind?",
            "A sheet is light cloth, so the wind lifts and folds it again and again. From far away that can look like a living thing."
        )
    ],
    "reeds": [
        (
            "Why do reeds make whispering sounds?",
            "Reeds are hollow and thin, so wind and moving water rub them together. That can sound like hissing if you are already scared."
        )
    ],
}
KNOWLEDGE_ORDER = ["shadow", "light", "sunrise", "attention", "vines", "laundry", "reeds"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    apparition = f["apparition_cfg"]
    reveal = f["reveal_cfg"]
    return [
        f'Write a short fable for a young child that includes the words "discourage" and "slay".',
        f"Tell a fable about {hero.id} the {hero.type}, who thinks {apparition.actual} is {apparition.seeming}, and about {helper.id} who tries to discourage a foolish attack.",
        f"Write a transformation story in which fear is changed by {reveal.label} into understanding, and end with a clear moral image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    apparition = f["apparition_cfg"]
    reveal = f["reveal_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the young {hero.type} and {helper.id} the {helper.attrs['status']} {helper.type}. They were walking in {place.label} when they saw a frightening shape."
        ),
        (
            f"What did {hero.id} think {hero.pronoun()} saw?",
            f"{hero.id} thought {hero.pronoun()} saw {apparition.seeming}. The dim evening made {apparition.actual} look much more dangerous than it really was."
        ),
        (
            f"How did {helper.id} try to discourage {hero.id}?",
            f"{helper.id} warned {hero.id} not to trust a shadow at dusk. {helper.pronoun().capitalize()} tried to slow the moment down so the truth could be seen before anyone struck."
        ),
    ]
    if outcome == "heeded":
        qa.append(
            (
                f"Why was it good that {hero.id} listened?",
                f"It was good because no one got hurt and the truth appeared as soon as they used {reveal.label}. {hero.id} changed from boastful to thoughtful before trouble began."
            )
        )
    else:
        stuck = world.facts["hero"].meters["stuck"] >= THRESHOLD
        second = (
            f"{hero.id} got tangled because {apparition.actual} caught at {hero.pronoun('possessive')} body when {hero.pronoun()} rushed in."
            if stuck
            else f"{hero.id} felt ashamed because the blow met only a harmless thing and made {hero.pronoun('object')} see {hero.pronoun('possessive')} mistake."
        )
        qa.append(
            (
                f"What happened when {hero.id} tried to slay the shape?",
                f"{hero.id} attacked before knowing the truth, and the moment turned foolish instead of brave. {second}"
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the frightening shape turning back into {apparition.actual} under {reveal.label}. That ending proves the real transformation was in {hero.id}'s understanding."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"shadow"} | set(f["reveal_cfg"].tags) | set(f["apparition_cfg"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="vineyard",
        apparition="vine_arch",
        reveal="lantern",
        hero_name="Pip",
        hero_type="goat",
        helper_name="Moss",
        helper_type="tortoise",
        helper_status="elder",
        hero_trait="bold",
    ),
    StoryParams(
        place="courtyard",
        apparition="laundry_sheet",
        reveal="closer_look",
        hero_name="Rill",
        hero_type="fox",
        helper_name="Pebble",
        helper_type="duck",
        helper_status="peer",
        hero_trait="careful",
    ),
    StoryParams(
        place="riverbank",
        apparition="reed_clump",
        reveal="sunrise",
        hero_name="Red",
        hero_type="rooster",
        helper_name="Ashfeather",
        helper_type="owl",
        helper_status="elder",
        hero_trait="vain",
    ),
    StoryParams(
        place="courtyard",
        apparition="laundry_sheet",
        reveal="lantern",
        hero_name="Bram",
        hero_type="goat",
        helper_name="Drift",
        helper_type="duck",
        helper_status="peer",
        hero_trait="rash",
    ),
]


ASP_RULES = r"""
misread_hazard(A) :- apparition(A), misreadable(A).
works(P, A, R) :- place(P), apparition(A), reveal(R),
                  affords(P, A), reveal_place(R, P),
                  confusion(A, C), clarity(R, K), K >= C.
valid(P, A, R) :- works(P, A, R), misread_hazard(A).

heeded :- chosen_trait(T), pride(T, P), chosen_helper_status(S), help_power(S, H), P <= H + 2.
outcome(heeded) :- heeded.
outcome(lunged) :- not heeded.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for apparition_id in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, apparition_id))
    for app_id, app in APPARITIONS.items():
        lines.append(asp.fact("apparition", app_id))
        lines.append(asp.fact("confusion", app_id, app.confusion))
        if app.misreadable:
            lines.append(asp.fact("misreadable", app_id))
    for reveal_id, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", reveal_id))
        lines.append(asp.fact("clarity", reveal_id, reveal.clarity))
        for place_id in sorted(reveal.place_ok):
            lines.append(asp.fact("reveal_place", reveal_id, place_id))
    for trait, pride in PRIDE_LEVEL.items():
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("pride", trait, pride))
    for status, power in HELPER_POWER.items():
        lines.append(asp.fact("helper_status", status))
        lines.append(asp.fact("help_power", status, power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_trait", params.hero_trait),
            asp.fact("chosen_helper_status", params.helper_status),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable world: a proud young animal mistakes an ordinary shape for a beast, and clear seeing transforms the conflict."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--apparition", choices=APPARITIONS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--hero-type", choices=sorted(HERO_NAMES))
    ap.add_argument("--helper-status", choices=sorted(HELPER_POWER))
    ap.add_argument("--hero-trait", choices=sorted(HERO_TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_helper(rng: random.Random, status: str) -> tuple[str, str]:
    species = rng.choice(sorted(HELPER_NAMES[status]))
    name = rng.choice(HELPER_NAMES[status][species])
    return name, species


def pick_hero(rng: random.Random, hero_type: str) -> str:
    return rng.choice(HERO_NAMES[hero_type])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_key = args.place
    apparition_key = args.apparition
    reveal_key = args.reveal

    if place_key is not None and place_key not in PLACES:
        raise StoryError(f"(No story: unknown place '{place_key}'.)")
    if apparition_key is not None and apparition_key not in APPARITIONS:
        raise StoryError(f"(No story: unknown apparition '{apparition_key}'.)")
    if reveal_key is not None and reveal_key not in REVEALS:
        raise StoryError(f"(No story: unknown reveal '{reveal_key}'.)")

    if place_key and apparition_key:
        place = PLACES[place_key]
        apparition = APPARITIONS[apparition_key]
        reveal = REVEALS[reveal_key] if reveal_key else None
        if apparition_key not in place.affordances or not apparition.misreadable or (reveal is not None and not reveal_works(place, apparition, reveal)):
            raise StoryError(explain_rejection(place, apparition, reveal))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.apparition is None or combo[1] == args.apparition)
        and (args.reveal is None or combo[2] == args.reveal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, apparition_id, reveal_id = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(sorted(HERO_NAMES))
    helper_status = args.helper_status or rng.choice(sorted(HELPER_POWER))
    hero_trait = args.hero_trait or rng.choice(HERO_TRAITS)
    hero_name = pick_hero(rng, hero_type)
    helper_name, helper_type = pick_helper(rng, helper_status)
    return StoryParams(
        place=place_id,
        apparition=apparition_id,
        reveal=reveal_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        helper_status=helper_status,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.apparition not in APPARITIONS:
        raise StoryError(f"(No story: unknown apparition '{params.apparition}'.)")
    if params.reveal not in REVEALS:
        raise StoryError(f"(No story: unknown reveal '{params.reveal}'.)")
    if params.hero_type not in HERO_NAMES:
        raise StoryError(f"(No story: unknown hero type '{params.hero_type}'.)")
    if params.helper_status not in HELPER_POWER:
        raise StoryError(f"(No story: unknown helper status '{params.helper_status}'.)")
    if params.hero_trait not in PRIDE_LEVEL:
        raise StoryError(f"(No story: unknown hero trait '{params.hero_trait}'.)")

    place = PLACES[params.place]
    apparition = APPARITIONS[params.apparition]
    reveal = REVEALS[params.reveal]
    if params.apparition not in place.affordances or not reveal_works(place, apparition, reveal):
        raise StoryError(explain_rejection(place, apparition, reveal))

    world = tell(
        place=place,
        apparition=apparition,
        reveal=reveal,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        helper_status=params.helper_status,
        hero_trait=params.hero_trait,
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
        print(f"{len(combos)} compatible (place, apparition, reveal) combos:\n")
        for place, apparition, reveal in combos:
            print(f"  {place:10} {apparition:14} {reveal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name}: {p.apparition} in {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
