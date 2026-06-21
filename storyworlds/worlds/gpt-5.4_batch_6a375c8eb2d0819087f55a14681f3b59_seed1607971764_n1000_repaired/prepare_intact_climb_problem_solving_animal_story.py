#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/prepare_intact_climb_problem_solving_animal_story.py
================================================================================

A standalone story world for a small animal-story domain: a young climber finds a
fallen egg and wants to hurry it back to a high nest. The helper must think ahead,
predict the danger, and help the hero prepare a soft carrying fix before the climb,
so the egg can stay intact.

This world models a simple problem-solving shape:

    find a fragile problem
    -> predict why the first impulse is risky
    -> prepare a sensible tool
    -> climb carefully
    -> end with an image proving what changed

The key reasonableness constraint is physical and explicit:
a climber must actually be able to climb the route, and the chosen carrier must
protect the egg enough for that nest's wobble and height.

Run it
------
    python storyworlds/worlds/gpt-5.4/prepare_intact_climb_problem_solving_animal_story.py
    python storyworlds/worlds/gpt-5.4/prepare_intact_climb_problem_solving_animal_story.py --place pine_nest --climber squirrel --bundle moss_pouch
    python storyworlds/worlds/gpt-5.4/prepare_intact_climb_problem_solving_animal_story.py --place vine_nest --climber raccoon
    python storyworlds/worlds/gpt-5.4/prepare_intact_climb_problem_solving_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/prepare_intact_climb_problem_solving_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/prepare_intact_climb_problem_solving_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4/prepare_intact_climb_problem_solving_animal_story.py --json
    python storyworlds/worlds/gpt-5.4/prepare_intact_climb_problem_solving_animal_story.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "hen"}
        male = {"father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    nest_owner: str
    ground_spot: str
    route_kind: str
    difficulty: int
    wobble: int
    branch_text: str
    ending_text: str
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
class Climber:
    id: str
    species: str
    style: str
    skills: dict[str, int]
    grip_text: str
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
class Bundle:
    id: str
    label: str
    phrase: str
    padding: int
    make_text: str
    carry_text: str
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
class Helper:
    id: str
    species: str
    idea_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
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
    place: str
    climber: str
    bundle: str
    helper: str
    hero_name: str
    helper_name: str
    approach: str = "careful"  # "careful" | "rush"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
        self.facts: dict = {
            "route_wobble": 0,
            "route_difficulty": 0,
            "approach": "",
            "predicted_crack": False,
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_unprotected_climb(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    egg = world.get("egg")
    if hero.meters["climbing"] < THRESHOLD or egg.meters["carried"] < THRESHOLD:
        return out
    if egg.attrs.get("protected", False):
        return out
    sig = ("jostle", int(hero.meters["climbing"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    egg.meters["crack_risk"] += float(world.facts["route_wobble"])
    hero.memes["fear"] += 1
    out.append("__jostle__")
    return out


def _r_crack(world: World) -> list[str]:
    out: list[str] = []
    egg = world.get("egg")
    if egg.meters["crack_risk"] < THRESHOLD:
        return out
    sig = ("crack",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    egg.meters["intact"] = 0.0
    egg.meters["cracked"] += 1.0
    world.get("hero").memes["sadness"] += 1
    world.get("helper_char").memes["sadness"] += 1
    out.append("__crack__")
    return out


def _r_safe_return(world: World) -> list[str]:
    out: list[str] = []
    egg = world.get("egg")
    if egg.meters["returned"] < THRESHOLD or egg.meters["intact"] < THRESHOLD:
        return out
    sig = ("safe_return",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["relief"] += 1
    world.get("helper_char").memes["relief"] += 1
    world.get("hero").memes["pride"] += 1
    out.append("__safe_return__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="unprotected_climb", tag="physical", apply=_r_unprotected_climb),
    Rule(name="crack", tag="physical", apply=_r_crack),
    Rule(name="safe_return", tag="social", apply=_r_safe_return),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def climb_skill(climber: Climber, place: Place) -> int:
    return climber.skills.get(place.route_kind, 0)


def can_climb(climber: Climber, place: Place) -> bool:
    return climb_skill(climber, place) >= place.difficulty


def bundle_safe(bundle: Bundle, place: Place) -> bool:
    return bundle.padding >= place.wobble


def valid_combo(place: Place, climber: Climber, bundle: Bundle) -> bool:
    return can_climb(climber, place) and bundle_safe(bundle, place)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for climber_id, climber in CLIMBERS.items():
            for bundle_id, bundle in BUNDLES.items():
                if valid_combo(place, climber, bundle):
                    combos.append((place_id, climber_id, bundle_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.climber not in CLIMBERS or params.bundle not in BUNDLES:
        raise StoryError("(Unknown place, climber, or bundle.)")
    place = PLACES[params.place]
    climber = CLIMBERS[params.climber]
    bundle = BUNDLES[params.bundle]
    if not valid_combo(place, climber, bundle):
        raise StoryError(explain_rejection(place, climber, bundle))
    return "intact" if params.approach == "careful" else "cracked"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def _do_climb(world: World, prepared: bool, narrate: bool = True) -> None:
    hero = world.get("hero")
    egg = world.get("egg")
    egg.attrs["protected"] = prepared
    egg.meters["carried"] += 1.0
    hero.meters["climbing"] += 1.0
    hero.memes["determined"] += 1.0
    propagate(world, narrate=narrate)


def predict_crack(world: World) -> bool:
    sim = world.copy()
    _do_climb(sim, prepared=False, narrate=False)
    return sim.get("egg").meters["intact"] < THRESHOLD


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, climber_cfg: Climber, helper_cfg: Helper) -> None:
    hero.memes["kindness"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{hero.id} the {climber_cfg.species} loved hard jobs that called for quick feet and bright eyes. "
        f"{helper.id} the {helper_cfg.species} was {helper_cfg.idea_text}, and together they liked helping small creatures."
    )


def find_egg(world: World, hero: Entity, place: Place) -> None:
    egg = world.get("egg")
    egg.meters["intact"] = 1.0
    world.say(
        f"One morning they found a little {place.nest_owner} egg resting in {place.ground_spot}, right under {place.branch_text}. "
        f"The shell was still intact, but it did not belong on the ground."
    )


def see_nest(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"{hero.id} looked up and spotted the nest high above. To reach it, someone would have to climb {place.label}."
    )


def impulse(world: World, hero: Entity, climber_cfg: Climber) -> None:
    hero.memes["eagerness"] += 1
    world.say(
        f'"I can do it right now," said {hero.id}. {climber_cfg.grip_text.capitalize()}, and the brave little climber was already ready to scramble upward.'
    )


def warning(world: World, hero: Entity, helper: Entity, place: Place, bundle: Bundle) -> None:
    cracked = predict_crack(world)
    helper.memes["worry"] += 1
    world.facts["predicted_crack"] = cracked
    if cracked:
        world.say(
            f'{helper.id} touched the egg with a careful paw. "Wait," {helper.pronoun()} said. '
            f'"If you climb with it bare in your paws, the shell may not stay intact. We should prepare {bundle.phrase} first."'
        )
    else:
        world.say(
            f'{helper.id} studied the climb. "Let us still prepare {bundle.phrase} first," {helper.pronoun()} said. '
            f'"Good helpers think before they hurry."'
        )


def rush_anyway(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"But {hero.id} was in such a hurry to help that {hero.pronoun()} tucked the egg close and began to climb at once."
    )
    _do_climb(world, prepared=False, narrate=False)
    egg = world.get("egg")
    if egg.meters["cracked"] >= THRESHOLD:
        world.say(
            f"Halfway up, {place.label} gave a wobble. The egg tapped against the bark, and a thin crack ran over the shell."
        )
    else:
        world.say(
            f"The climb was awkward and shaky, but somehow the egg held together."
        )


def prepare_bundle(world: World, hero: Entity, helper: Entity, bundle: Bundle) -> None:
    egg = world.get("egg")
    egg.attrs["planned_bundle"] = bundle.id
    hero.memes["patience"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"So the two friends stopped to prepare. {bundle.make_text.capitalize()}, making a soft little nest that fit the egg just right."
    )


def careful_climb(world: World, hero: Entity, place: Place, bundle: Bundle) -> None:
    world.say(
        f"{hero.id} set the egg in {bundle.phrase}, held it close, and started to climb {place.label} with slow, sure movements."
    )
    _do_climb(world, prepared=True, narrate=False)
    world.say(
        f"Step by step, {hero.pronoun()} kept to the safest holds until {hero.pronoun()} reached the nest."
    )


def return_egg(world: World, hero: Entity, place: Place) -> None:
    egg = world.get("egg")
    egg.meters["returned"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tucked the egg beside the warm feathers and stepped back. It was still intact."
    )
    world.say(place.ending_text)


def cracked_resolution(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"{hero.id} climbed back down slowly, and {helper.id} spread leaves in a low, safe hollow so the egg would not roll again."
    )
    world.say(
        f'Together they called up to the worried {place.nest_owner} parent and promised, "Next time we will prepare before we climb."'
    )


def wise_ending(world: World, hero: Entity, helper: Entity, bundle: Bundle) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"From then on, whenever a job was small and fragile, {hero.id} did not dash first. {hero.pronoun().capitalize()} stopped to prepare, and {helper.id} grinned every time."
    )
    world.say(
        f"Below the tree, {bundle.label} rested in the grass, and above it the nest sat quiet and safe."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    *,
    place: Place,
    climber: Climber,
    bundle: Bundle,
    helper_cfg: Helper,
    hero_name: str,
    helper_name: str,
    approach: str,
) -> World:
    world = World()
    world.facts["route_wobble"] = place.wobble
    world.facts["route_difficulty"] = place.difficulty
    world.facts["approach"] = approach

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=climber.species,
        label=hero_name,
        role="hero",
        traits=[climber.style],
        tags=set(climber.tags),
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper_char",
        kind="character",
        type=helper_cfg.species,
        label=helper_name,
        role="helper",
        traits=["thoughtful"],
        tags=set(helper_cfg.tags),
        attrs={},
    ))
    egg = world.add(Entity(
        id="egg",
        kind="thing",
        type="egg",
        label=f"{place.nest_owner} egg",
        role="egg",
        attrs={"protected": False, "planned_bundle": ""},
        tags={"egg", "fragile"},
    ))
    nest = world.add(Entity(
        id="nest",
        kind="thing",
        type="nest",
        label="nest",
        role="nest",
        attrs={"owner": place.nest_owner},
        tags={"nest"},
    ))

    world.facts.update(
        place=place,
        climber=climber,
        bundle=bundle,
        helper_cfg=helper_cfg,
        hero=hero,
        helper=helper,
        egg=egg,
        nest=nest,
    )

    introduce(world, hero, helper, climber, helper_cfg)
    find_egg(world, hero, place)
    see_nest(world, hero, place)

    world.para()
    impulse(world, hero, climber)
    warning(world, hero, helper, place, bundle)

    world.para()
    if approach == "rush":
        rush_anyway(world, hero, place)
        if egg.meters["intact"] >= THRESHOLD:
            return_egg(world, hero, place)
            world.para()
            wise_ending(world, hero, helper, bundle)
            world.facts["outcome"] = "intact"
        else:
            cracked_resolution(world, hero, helper, place)
            world.facts["outcome"] = "cracked"
    else:
        prepare_bundle(world, hero, helper, bundle)
        careful_climb(world, hero, place, bundle)
        return_egg(world, hero, place)
        world.para()
        wise_ending(world, hero, helper, bundle)
        world.facts["outcome"] = "intact"

    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "oak_nest": Place(
        id="oak_nest",
        label="the rough old oak",
        nest_owner="sparrow",
        ground_spot="a ring of clover",
        route_kind="bark",
        difficulty=2,
        wobble=1,
        branch_text="the low, wide branches of the old oak",
        ending_text="A sparrow fluttered down, then back up again, and settled over the egg with a pleased little chirp.",
        tags={"tree", "oak", "nest"},
    ),
    "pine_nest": Place(
        id="pine_nest",
        label="the tall pine",
        nest_owner="robin",
        ground_spot="the soft needles at the root of the pine",
        route_kind="bark",
        difficulty=3,
        wobble=2,
        branch_text="the thin, windy branches of the tall pine",
        ending_text="The robin parent landed on the nest, turned the egg gently, and sang once into the breeze.",
        tags={"tree", "pine", "wind"},
    ),
    "vine_nest": Place(
        id="vine_nest",
        label="the willow and its hanging vines",
        nest_owner="wren",
        ground_spot="a patch of moss beside the roots",
        route_kind="vine",
        difficulty=2,
        wobble=2,
        branch_text="the drooping willow branches above the pond",
        ending_text="The wren parent hopped into the nest and tucked the egg under one wing as the vines swayed softly.",
        tags={"willow", "vine", "pond"},
    ),
    "loft_nest": Place(
        id="loft_nest",
        label="the old barn ladder to the loft beam",
        nest_owner="swallow",
        ground_spot="the sweet hay below the ladder",
        route_kind="beam",
        difficulty=1,
        wobble=1,
        branch_text="the beams under the barn roof",
        ending_text="Above the hay, the swallow parent slipped into the nest and rustled happily for a long moment.",
        tags={"barn", "ladder", "loft"},
    ),
}

CLIMBERS = {
    "squirrel": Climber(
        id="squirrel",
        species="squirrel",
        style="nimble",
        skills={"bark": 3, "vine": 2, "beam": 1},
        grip_text="its toes loved bark and branch",
        tags={"squirrel", "climb"},
    ),
    "raccoon": Climber(
        id="raccoon",
        species="raccoon",
        style="steady",
        skills={"bark": 2, "vine": 1, "beam": 2},
        grip_text="its clever paws were strong but a little heavy",
        tags={"raccoon", "climb"},
    ),
    "monkey": Climber(
        id="monkey",
        species="monkey",
        style="springy",
        skills={"bark": 2, "vine": 3, "beam": 2},
        grip_text="its tail and hands worked together like a team",
        tags={"monkey", "climb"},
    ),
}

BUNDLES = {
    "moss_pouch": Bundle(
        id="moss_pouch",
        label="moss pouch",
        phrase="a moss pouch",
        padding=2,
        make_text="they lined a curled leaf with moss and tied it with grass",
        carry_text="held the soft pouch against the chest",
        tags={"moss", "pouch", "soft"},
    ),
    "bark_basket": Bundle(
        id="bark_basket",
        label="bark basket",
        phrase="a tiny bark basket",
        padding=3,
        make_text="they bent a strip of loose bark into a tiny basket and packed it with dry feathers",
        carry_text="balanced the basket very carefully",
        tags={"basket", "bark", "feathers"},
    ),
    "leaf_sling": Bundle(
        id="leaf_sling",
        label="leaf sling",
        phrase="a leaf sling",
        padding=1,
        make_text="they folded a broad leaf and looped it with plant fiber",
        carry_text="kept the sling snug and still",
        tags={"leaf", "sling"},
    ),
}

HELPERS = {
    "rabbit": Helper(
        id="rabbit",
        species="rabbit",
        idea_text="good at stopping to think before a leap",
        tags={"rabbit", "thinking"},
    ),
    "beaver": Helper(
        id="beaver",
        species="beaver",
        idea_text="famous for planning useful little fixes",
        tags={"beaver", "planning"},
    ),
    "mouse": Helper(
        id="mouse",
        species="mouse",
        idea_text="small, calm, and full of smart ideas",
        tags={"mouse", "planning"},
    ),
}

NAMES = {
    "squirrel": ["Pip", "Hazel", "Nim", "Tumble"],
    "raccoon": ["Moss", "Pebble", "Rook", "Mimi"],
    "monkey": ["Jori", "Pico", "Luma", "Bibi"],
    "rabbit": ["Fern", "Poppy", "Thimble", "Hopper"],
    "beaver": ["Maple", "Chip", "Willow", "Reed"],
    "mouse": ["Dot", "Pipkin", "Squeak", "Tansy"],
}


# ---------------------------------------------------------------------------
# Q&A knowledge
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "egg": [
        (
            "Why must an egg be carried gently?",
            "An egg has a hard shell, but the shell can still crack if it gets bumped or dropped. Carrying it gently keeps what is inside safe.",
        )
    ],
    "nest": [
        (
            "Why do birds keep eggs in nests?",
            "A nest holds eggs in one soft place and helps keep them from rolling away. It also lets the parent bird sit on them and keep them warm.",
        )
    ],
    "climb": [
        (
            "Why can climbing with full paws be tricky?",
            "Climbing safely often takes balance and a good grip. If your paws are busy carrying something fragile, it is easier to wobble or bump it.",
        )
    ],
    "moss": [
        (
            "Why is moss good for padding?",
            "Moss is soft and springy, so it can cushion a delicate thing. That makes bumps feel gentler.",
        )
    ],
    "basket": [
        (
            "What does a basket do for a fragile object?",
            "A basket keeps a small object in one place instead of letting it slide around. If it is padded too, it protects the object even more.",
        )
    ],
    "leaf": [
        (
            "Why might one leaf not be enough to protect an egg?",
            "A single leaf is soft, but it is also thin and floppy. On a bouncy climb, thin padding may not stop a hard bump.",
        )
    ],
    "wind": [
        (
            "Why are high branches harder on a windy day?",
            "Wind can make thin branches sway and wobble. That makes careful carrying much harder.",
        )
    ],
    "planning": [
        (
            "What does it mean to prepare for a hard job?",
            "To prepare means to get ready before you start. You think about the problem, gather what you need, and make the job safer and easier.",
        )
    ],
}
KNOWLEDGE_ORDER = ["egg", "nest", "climb", "planning", "moss", "basket", "leaf", "wind"]


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    climber = world.facts["climber"]
    helper = world.facts["helper_cfg"]
    bundle = world.facts["bundle"]
    outcome = world.facts["outcome"]
    if outcome == "intact":
        return [
            f'Write a short animal story for a 3-to-5-year-old that includes the words "prepare", "intact", and "climb".',
            f"Tell a gentle problem-solving story where a {climber.species} and a {helper.species} find a fallen egg, stop to prepare {bundle.phrase}, and climb {place.label} to return it safely.",
            f"Write a simple animal story with a high nest, a fragile egg, and a smart plan that keeps the egg intact.",
        ]
    return [
        f'Write a short animal story for a 3-to-5-year-old that includes the words "prepare", "intact", and "climb".',
        f"Tell a cautionary animal story where a {climber.species} rushes to climb before preparing a safe carrier for a fallen egg.",
        f"Write a problem-solving story that shows why hurrying is not the same thing as helping.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    climber = world.facts["climber"]
    helper_cfg = world.facts["helper_cfg"]
    bundle = world.facts["bundle"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} the {climber.species} and {helper.label} the {helper_cfg.species}. They were trying to help a lost egg get back to its nest.",
        ),
        (
            "What problem did they find?",
            f"They found a little {place.nest_owner} egg on the ground under {place.label}. The egg was still intact, but it needed to go back up to the nest.",
        ),
        (
            f"Why did {helper.label} tell {hero.label} to prepare first?",
            f"{helper.label} could see that climbing with a bare egg would be shaky and risky. {helper.pronoun().capitalize()} wanted to protect the shell before the climb, not after a crack had already happened.",
        ),
    ]
    if outcome == "intact":
        qa.extend(
            [
                (
                    f"How did they solve the problem?",
                    f"They stopped to prepare {bundle.phrase} and padded it before the climb. That gave the egg a soft place to rest while {hero.label} carried it back up.",
                ),
                (
                    f"Why did the egg stay intact?",
                    f"The egg stayed intact because the friends solved the problem before hurrying into it. The padding protected the shell while {hero.label} climbed.",
                ),
                (
                    "How did the story end?",
                    f"It ended with the egg safe in the nest and the parent {place.nest_owner} returning to it. The last image shows that careful thinking changed the whole day.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"What happened when {hero.label} rushed to climb?",
                    f"{hero.label} hurried up without the planned padding, and the egg got bumped on the way. The crack happened because helping fast was not the same as helping carefully.",
                ),
                (
                    "What did the friends learn?",
                    f"They learned that kind intentions are not enough by themselves. For fragile jobs, it is wiser to prepare first and then climb.",
                ),
                (
                    "How did the story end?",
                    f"It ended with the friends making the egg safe on the ground and promising to plan better next time. The ending shows a real change in how they will solve problems from then on.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"egg", "nest", "climb", "planning"}
    place = world.facts["place"]
    bundle = world.facts["bundle"]
    tags |= set(place.tags)
    tags |= set(bundle.tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  world_facts={world.facts['approach']}, wobble={world.facts['route_wobble']}, difficulty={world.facts['route_difficulty']}, predicted_crack={world.facts['predicted_crack']}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Rejections
# ---------------------------------------------------------------------------
def explain_rejection(place: Place, climber: Climber, bundle: Bundle) -> str:
    if not can_climb(climber, place):
        return (
            f"(No story: a {climber.species} is not a good fit for {place.label}. "
            f"The route needs more {place.route_kind}-climbing skill.)"
        )
    if not bundle_safe(bundle, place):
        return (
            f"(No story: {bundle.phrase} is too flimsy for {place.label}. "
            f"The climb wobbles too much to keep the egg intact.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
can_climb(C,P) :- skill(C,R,S), route(P,R), difficulty(P,D), S >= D.
safe_bundle(B,P) :- padding(B,Pad), wobble(P,W), Pad >= W.
valid(P,C,B) :- place(P), climber(C), bundle(B), can_climb(C,P), safe_bundle(B,P).

outcome(intact) :- chosen_place(P), chosen_climber(C), chosen_bundle(B),
                   chosen_approach(careful), valid(P,C,B).
outcome(cracked) :- chosen_place(P), chosen_climber(C),
                    chosen_approach(rush), can_climb(C,P).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("route", pid, place.route_kind))
        lines.append(asp.fact("difficulty", pid, place.difficulty))
        lines.append(asp.fact("wobble", pid, place.wobble))
    for cid, climber in CLIMBERS.items():
        lines.append(asp.fact("climber", cid))
        for route, skill in sorted(climber.skills.items()):
            lines.append(asp.fact("skill", cid, route, skill))
    for bid, bundle in BUNDLES.items():
        lines.append(asp.fact("bundle", bid))
        lines.append(asp.fact("padding", bid, bundle.padding))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_climber", params.climber),
            asp.fact("chosen_bundle", params.bundle),
            asp.fact("chosen_approach", params.approach),
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


# ---------------------------------------------------------------------------
# Content curation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="oak_nest",
        climber="squirrel",
        bundle="leaf_sling",
        helper="rabbit",
        hero_name="Pip",
        helper_name="Fern",
        approach="careful",
    ),
    StoryParams(
        place="pine_nest",
        climber="squirrel",
        bundle="moss_pouch",
        helper="mouse",
        hero_name="Hazel",
        helper_name="Dot",
        approach="careful",
    ),
    StoryParams(
        place="vine_nest",
        climber="monkey",
        bundle="bark_basket",
        helper="beaver",
        hero_name="Jori",
        helper_name="Maple",
        approach="careful",
    ),
    StoryParams(
        place="loft_nest",
        climber="raccoon",
        bundle="leaf_sling",
        helper="rabbit",
        hero_name="Pebble",
        helper_name="Poppy",
        approach="careful",
    ),
    StoryParams(
        place="pine_nest",
        climber="squirrel",
        bundle="moss_pouch",
        helper="rabbit",
        hero_name="Nim",
        helper_name="Thimble",
        approach="rush",
    ),
]


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: return a fallen egg by solving a climbing problem sensibly."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--climber", choices=sorted(CLIMBERS))
    ap.add_argument("--bundle", choices=sorted(BUNDLES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--approach", choices=["careful", "rush"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, climber, bundle) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.climber and args.bundle:
        place = PLACES[args.place]
        climber = CLIMBERS[args.climber]
        bundle = BUNDLES[args.bundle]
        if not valid_combo(place, climber, bundle):
            raise StoryError(explain_rejection(place, climber, bundle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.climber is None or combo[1] == args.climber)
        and (args.bundle is None or combo[2] == args.bundle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, climber_id, bundle_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_name = args.hero_name or rng.choice([n for n in NAMES[climber_id]])
    helper_name = args.helper_name or rng.choice([n for n in NAMES[helper_id] if n != hero_name])
    approach = args.approach or rng.choice(["careful", "careful", "careful", "rush"])

    return StoryParams(
        place=place_id,
        climber=climber_id,
        bundle=bundle_id,
        helper=helper_id,
        hero_name=hero_name,
        helper_name=helper_name,
        approach=approach,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.climber not in CLIMBERS:
        raise StoryError(f"(Unknown climber: {params.climber})")
    if params.bundle not in BUNDLES:
        raise StoryError(f"(Unknown bundle: {params.bundle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.approach not in {"careful", "rush"}:
        raise StoryError(f"(Unknown approach: {params.approach})")

    place = PLACES[params.place]
    climber = CLIMBERS[params.climber]
    bundle = BUNDLES[params.bundle]
    helper_cfg = HELPERS[params.helper]

    if not valid_combo(place, climber, bundle):
        raise StoryError(explain_rejection(place, climber, bundle))

    world = tell(
        place=place,
        climber=climber,
        bundle=bundle,
        helper_cfg=helper_cfg,
        hero_name=params.hero_name,
        helper_name=params.helper_name,
        approach=params.approach,
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


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combo gate matches ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
        except StoryError:
            rc = 1
            print("Python outcome failed unexpectedly for:", params)
            bad += 1
            continue
        asp_res = asp_outcome(params)
        if py != asp_res:
            bad += 1
            print(f"MISMATCH outcome for {params}: python={py} asp={asp_res}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        sample = generate(resolve_params(parser.parse_args([]), random.Random(123)))
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        if not sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: default generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
        print("OK: curated generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"CURATED SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, climber, bundle) combos:\n")
        for place, climber, bundle in combos:
            print(f"  {place:10} {climber:8} {bundle}")
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
            header = f"### {p.hero_name} the {p.climber}: {p.place} with {p.bundle} ({p.approach})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
