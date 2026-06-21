#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/egg_dim_lesson_learned_nursery_rhyme.py
==================================================================

A standalone story world for a tiny nursery-rhyme-shaped lesson tale:

A child steps into an egg-dim morning coop, tries to carry too many eggs or
carry them the wrong way, hears a warning, cracks an egg, learns to go slowly,
then makes a safer second trip.

The world model keeps track of:
- physical meters: wobble, rattle, cracked, gathered, safe_trip
- emotional memes: hurry, worry, shame, comfort, pride, patience

The reasonableness gate refuses combinations that have no honest hazard or no
plausible safer fix. The ASP twin mirrors that gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/egg_dim_lesson_learned_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/egg_dim_lesson_learned_nursery_rhyme.py --place coop --path stones --carrier tin_pail --load 4
    python storyworlds/worlds/gpt-5.4/egg_dim_lesson_learned_nursery_rhyme.py --carrier egg_crate --load 2
    python storyworlds/worlds/gpt-5.4/egg_dim_lesson_learned_nursery_rhyme.py --all --qa
    python storyworlds/worlds/gpt-5.4/egg_dim_lesson_learned_nursery_rhyme.py --asp
    python storyworlds/worlds/gpt-5.4/egg_dim_lesson_learned_nursery_rhyme.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class Place:
    id: str
    label: str
    opening: str
    hens: str
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
class Path:
    id: str
    label: str
    texture: str
    bump: int
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
class Carrier:
    id: str
    label: str
    phrase: str
    capacity: int
    stability: int
    padded: bool
    sense: int
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
class StoryParams:
    place: str = "coop"
    path: str = "stones"
    carrier: str = "tin_pail"
    load: int = 4
    hero_name: str = "Pip"
    hero_gender: str = "boy"
    helper_name: str = "Nan"
    helper_type: str = "grandmother"
    trait: str = "hasty"
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


def _r_overload(world: World) -> list[str]:
    out: list[str] = []
    carrier = world.get("carrier")
    eggs = world.get("eggs")
    if eggs.meters["gathered"] < THRESHOLD:
        return out
    if eggs.attrs["count"] <= carrier.attrs["capacity"]:
        return out
    sig = ("overload", carrier.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carrier.meters["wobble"] += 1
    world.get("hero").memes["worry"] += 1
    world.facts.setdefault("risk_reasons", []).append("too_many")
    out.append("__overload__")
    return out


def _r_rattle(world: World) -> list[str]:
    out: list[str] = []
    carrier = world.get("carrier")
    eggs = world.get("eggs")
    path = world.get("path")
    if eggs.meters["gathered"] < THRESHOLD:
        return out
    if carrier.attrs["padded"]:
        return out
    if path.attrs["bump"] <= carrier.attrs["stability"]:
        return out
    sig = ("rattle", carrier.id, path.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carrier.meters["rattle"] += 1
    world.get("hero").memes["worry"] += 1
    world.facts.setdefault("risk_reasons", []).append("hard_rattle")
    out.append("__rattle__")
    return out


def _r_crack(world: World) -> list[str]:
    out: list[str] = []
    carrier = world.get("carrier")
    eggs = world.get("eggs")
    if carrier.meters["wobble"] < THRESHOLD and carrier.meters["rattle"] < THRESHOLD:
        return out
    sig = ("crack", eggs.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    eggs.meters["cracked"] += 1
    world.get("hero").memes["shame"] += 1
    world.get("helper").memes["comfort"] += 1
    world.facts["egg_cracked"] = True
    out.append("__crack__")
    return out


CAUSAL_RULES = [
    Rule(name="overload", tag="physical", apply=_r_overload),
    Rule(name="rattle", tag="physical", apply=_r_rattle),
    Rule(name="crack", tag="physical", apply=_r_crack),
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


PLACES = {
    "coop": Place(
        id="coop",
        label="the coop",
        opening="In the egg-dim coop, where the dawn was gray,",
        hens="the hens made soft little clucks in the hay",
        affords={"stones", "moss", "boards"},
        tags={"hens", "dawn"},
    ),
    "barn_nest": Place(
        id="barn_nest",
        label="the barn nest-room",
        opening="In the egg-dim barn, with a whispering beam,",
        hens="the hens blinked slow as if still in a dream",
        affords={"boards", "moss"},
        tags={"hens", "barn"},
    ),
    "garden_hutch": Place(
        id="garden_hutch",
        label="the garden hutch",
        opening="By the egg-dim hutch, in the pearly light,",
        hens="the hens tucked their feathers and rustled just right",
        affords={"stones", "moss"},
        tags={"hens", "garden"},
    ),
}

PATHS = {
    "stones": Path(
        id="stones",
        label="the stepping stones",
        texture="little stones with hop-hop bumps",
        bump=3,
        tags={"path", "stones"},
    ),
    "boards": Path(
        id="boards",
        label="the porch boards",
        texture="boards that creaked but stayed mostly level",
        bump=2,
        tags={"path", "boards"},
    ),
    "moss": Path(
        id="moss",
        label="the mossy lane",
        texture="soft moss that drank up each footstep",
        bump=1,
        tags={"path", "moss"},
    ),
}

CARRIERS = {
    "apron_fold": Carrier(
        id="apron_fold",
        label="apron fold",
        phrase="an apron fold held up in two small hands",
        capacity=2,
        stability=1,
        padded=False,
        sense=1,
        tags={"apron"},
    ),
    "tin_pail": Carrier(
        id="tin_pail",
        label="tin pail",
        phrase="a bright tin pail",
        capacity=4,
        stability=1,
        padded=False,
        sense=1,
        tags={"pail", "metal"},
    ),
    "willow_basket": Carrier(
        id="willow_basket",
        label="willow basket",
        phrase="a willow basket lined with a folded cloth",
        capacity=4,
        stability=2,
        padded=True,
        sense=3,
        tags={"basket", "cloth"},
    ),
    "egg_crate": Carrier(
        id="egg_crate",
        label="egg crate",
        phrase="a little egg crate with snug round cups",
        capacity=6,
        stability=3,
        padded=True,
        sense=4,
        tags={"crate", "careful"},
    ),
}

LOAD_CHOICES = [2, 4, 6]
TRAITS = ["hasty", "bouncy", "eager", "careful", "steady", "gentle"]
GIRL_NAMES = ["Pip", "Dot", "May", "Nell", "Wren", "Tess", "Molly", "June"]
BOY_NAMES = ["Pip", "Tom", "Ned", "Finn", "Kit", "Jem", "Leo", "Will"]
HELPER_NAMES = ["Nan", "Gran", "Moss", "Mim", "Rose", "Poppy", "Jo"]
HELPER_TYPES = ["grandmother", "mother", "grandfather", "father"]


def risky(carrier: Carrier, path: Path, load: int) -> bool:
    return load > carrier.capacity or (not carrier.padded and path.bump > carrier.stability)


def safe_for(carrier: Carrier, path: Path, load: int) -> bool:
    return load <= carrier.capacity and (carrier.padded or path.bump <= carrier.stability)


def better_carriers(path: Path, load: int, chosen: Carrier) -> list[Carrier]:
    out = []
    for carrier in CARRIERS.values():
        if carrier.id == chosen.id:
            continue
        if safe_for(carrier, path, load):
            out.append(carrier)
    return sorted(out, key=lambda c: (-c.sense, c.capacity, c.id))


def best_fix(path: Path, load: int, chosen: Carrier) -> Optional[Carrier]:
    options = better_carriers(path, load, chosen)
    return options[0] if options else None


def valid_combos() -> list[tuple[str, str, str, int]]:
    combos: list[tuple[str, str, str, int]] = []
    for place_id, place in PLACES.items():
        for path_id in sorted(place.affords):
            path = PATHS[path_id]
            for carrier_id, carrier in CARRIERS.items():
                for load in LOAD_CHOICES:
                    if risky(carrier, path, load) and best_fix(path, load, carrier) is not None:
                        combos.append((place_id, path_id, carrier_id, load))
    return sorted(combos)


def explain_rejection(place: Place, path: Path, carrier: Carrier, load: int) -> str:
    if path.id not in place.affords:
        return (
            f"(No story: {place.label} does not lead onto {path.label} in this world, "
            f"so that route is not available.)"
        )
    if not risky(carrier, path, load):
        return (
            f"(No story: {carrier.phrase} on {path.label} with {load} eggs is already "
            f"safe enough, so there is no honest warning and no lesson to learn.)"
        )
    return (
        f"(No story: {carrier.phrase} with {load} eggs on {path.label} is risky, but "
        f"this world knows no better carrier for that case, so it refuses to fake a fix.)"
    )


def predict_break(place: Place, path: Path, carrier: Carrier, load: int) -> dict:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type="girl", label="hero"))
    helper = world.add(Entity(id="helper", kind="character", type="grandmother", label="helper"))
    eggs = world.add(Entity(id="eggs", type="eggs", label="eggs", attrs={"count": load}))
    carrier_ent = world.add(
        Entity(
            id="carrier",
            type="carrier",
            label=carrier.label,
            attrs={
                "capacity": carrier.capacity,
                "stability": carrier.stability,
                "padded": carrier.padded,
            },
        )
    )
    path_ent = world.add(
        Entity(
            id="path",
            type="path",
            label=path.label,
            attrs={"bump": path.bump},
        )
    )
    eggs.meters["gathered"] = 1
    hero.memes["worry"] = 0.0
    helper.memes["comfort"] = 0.0
    world.facts["risk_reasons"] = []
    world.facts["egg_cracked"] = False
    propagate(world, narrate=False)
    return {
        "cracked": eggs.meters["cracked"] >= THRESHOLD,
        "reasons": list(world.facts["risk_reasons"]),
    }


def choose_opening_detail(hero: Entity, helper: Entity, place: Place) -> str:
    return (
        f"{place.opening} and {place.hens}. {hero.id} went tiptoe-tip, while "
        f"{helper.id} smiled by the door."
    )


def introduce(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    world.say(choose_opening_detail(hero, helper, place))
    world.say(
        f'"Eggs for the batter, eggs for the bread," sang {helper.id}, '
        f'"but mind your hands and mind your tread."'
    )


def gather_goal(world: World, hero: Entity, load: int) -> None:
    hero.memes["hurry"] += 1
    many = {2: "a pair", 4: "four", 6: "six"}[load]
    world.say(
        f"{hero.id} wanted {many} eggs in one quick round. A quick heart beat in "
        f"{hero.pronoun('possessive')} chest, because helping felt grand."
    )


def choose_carrier(world: World, hero: Entity, carrier: Carrier, path: Path) -> None:
    world.say(
        f"{hero.id} chose {carrier.phrase} and set off along {path.label}, "
        f"{path.texture} underfoot."
    )


def warn(world: World, helper: Entity, hero: Entity, carrier: Carrier, path: Path, load: int) -> None:
    pred = predict_break(world.place, path, carrier, load)
    world.facts["predicted_reasons"] = list(pred["reasons"])
    if "too_many" in pred["reasons"] and "hard_rattle" in pred["reasons"]:
        reason = "Too many eggs and too much clatter make a poor pair."
    elif "too_many" in pred["reasons"]:
        reason = "Too many eggs in one small hold make a wobbly load."
    else:
        reason = "Hard bumps and a bare little bucket make tender shells knock."
    world.say(
        f'"Slowly, slowly," said {helper.id}. "{reason} Better a small safe trip '
        f'than a fast one with a crack."'
    )


def set_off(world: World, hero: Entity) -> None:
    hero.memes["hurry"] += 1
    world.say(
        f"But {hero.id} thought, just for a blink, that quicker would be cleverer. "
        f"{hero.pronoun().capitalize()} stepped out before the warning had cooled."
    )


def accident(world: World, hero: Entity, helper: Entity, eggs: Entity, carrier_ent: Entity, path: Path) -> None:
    eggs.meters["gathered"] += 1
    propagate(world, narrate=False)
    pieces: list[str] = []
    if carrier_ent.meters["wobble"] >= THRESHOLD:
        pieces.append("The load gave a little wobble-wobble sway")
    if carrier_ent.meters["rattle"] >= THRESHOLD:
        pieces.append(f"{path.label.capitalize()} made a clink-clink rattle")
    if not pieces:
        pieces.append("The morning made one surprising slip")
    world.say(". ".join(pieces) + ".")
    world.say(
        "Then came a tiny tap and a softer crack. One egg wept a yellow tear down the side."
    )
    hero.memes["patience"] = 0.0
    helper.memes["comfort"] += 1


def comfort_and_lesson(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["comfort"] += 1
    hero.memes["patience"] += 1
    world.say(
        f'{hero.id} stopped still, with warm cheeks and sorry eyes. But {helper.id} '
        f'knelt down and said, "A broken egg is not a broken child."'
    )
    world.say(
        f'"Now you know what the shells were saying: gentle hands, gentle steps, '
        f'and not too much at once."'
    )


def retry(world: World, hero: Entity, helper: Entity, good_carrier: Carrier, load: int, path: Path) -> None:
    hero.memes["pride"] += 1
    hero.memes["patience"] += 1
    eggs = world.get("eggs")
    eggs.attrs["count"] = load
    eggs.meters["safe_trip"] += 1
    world.say(
        f'{helper.id} brought {good_carrier.phrase}. Together they tucked the eggs in, '
        f'round by round, so each shell had a quiet bed.'
    )
    world.say(
        f"This time {hero.id} walked hush-hush over {path.label}. No clink, no wobble, "
        f"no crack at all."
    )
    world.say(
        f"And when the bowl was filled at last, {hero.id} grinned and said, "
        f'"Slow and steady keeps breakfast ready."'
    )


def tell(
    place: Place,
    path: Path,
    chosen_carrier: Carrier,
    load: int,
    hero_name: str = "Pip",
    hero_gender: str = "boy",
    helper_name: str = "Nan",
    helper_type: str = "grandmother",
    trait: str = "hasty",
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            label=helper_name,
            role="helper",
        )
    )
    eggs = world.add(
        Entity(
            id="eggs",
            type="eggs",
            label="eggs",
            attrs={"count": load},
        )
    )
    carrier_ent = world.add(
        Entity(
            id="carrier",
            type="carrier",
            label=chosen_carrier.label,
            attrs={
                "capacity": chosen_carrier.capacity,
                "stability": chosen_carrier.stability,
                "padded": chosen_carrier.padded,
            },
        )
    )
    world.add(
        Entity(
            id="path",
            type="path",
            label=path.label,
            attrs={"bump": path.bump},
        )
    )

    hero.memes["hurry"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["shame"] = 0.0
    hero.memes["comfort"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["patience"] = 0.0
    helper.memes["comfort"] = 0.0
    eggs.meters["gathered"] = 0.0
    eggs.meters["cracked"] = 0.0
    eggs.meters["safe_trip"] = 0.0
    carrier_ent.meters["wobble"] = 0.0
    carrier_ent.meters["rattle"] = 0.0
    world.facts["risk_reasons"] = []
    world.facts["predicted_reasons"] = []
    world.facts["egg_cracked"] = False

    fix = best_fix(path, load, chosen_carrier)
    if fix is None:
        raise StoryError(explain_rejection(place, path, chosen_carrier, load))

    introduce(world, hero, helper, place)
    gather_goal(world, hero, load)

    world.para()
    choose_carrier(world, hero, chosen_carrier, path)
    warn(world, helper, hero, chosen_carrier, path, load)
    set_off(world, hero)

    world.para()
    accident(world, hero, helper, eggs, carrier_ent, path)
    comfort_and_lesson(world, hero, helper)

    world.para()
    retry(world, hero, helper, fix, load, path)

    world.facts.update(
        hero=hero,
        helper=helper,
        place=place,
        path_cfg=path,
        carrier_cfg=chosen_carrier,
        fix_cfg=fix,
        load=load,
        lesson="Slow and steady keeps breakfast ready.",
    )
    return world


KNOWLEDGE = {
    "hens": [
        (
            "Where do eggs come from on a farm?",
            "Eggs come from hens. A hen lays an egg with a hard shell around the soft part inside.",
        )
    ],
    "dawn": [
        (
            "What does dawn mean?",
            "Dawn is the very start of morning, when the sky begins to brighten after night.",
        )
    ],
    "path": [
        (
            "Why can bumps be a problem when you carry eggs?",
            "Eggs have thin shells, so hard bumps can knock them together. That is why people carry them gently and keep them from rattling.",
        )
    ],
    "basket": [
        (
            "Why is a lined basket good for eggs?",
            "A lined basket gives the eggs a softer place to rest. Soft padding helps stop little knocks from turning into cracks.",
        )
    ],
    "crate": [
        (
            "What does an egg crate do?",
            "An egg crate holds each egg in its own little cup. That keeps the eggs apart so they do not bump and break.",
        )
    ],
    "apron": [
        (
            "Why is an apron fold not the best place for many eggs?",
            "An apron fold can sag and sway when you walk. It may be fine for a very small thing, but many eggs need steadier support.",
        )
    ],
    "pail": [
        (
            "Why is a tin pail noisy for eggs?",
            "Tin is hard, and hard sides make more knocking when something bumps inside. Quiet, soft carriers are kinder to fragile shells.",
        )
    ],
    "careful": [
        (
            "What does it mean to be careful?",
            "Being careful means moving slowly enough to notice what might go wrong. Careful hands protect delicate things.",
        )
    ],
}
KNOWLEDGE_ORDER = ["hens", "dawn", "path", "basket", "crate", "apron", "pail", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    carrier = f["carrier_cfg"]
    return [
        'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the word "egg-dim" and teaches a lesson about going carefully.',
        f"Tell a gentle rhyme-story where {hero.id} carries eggs in {carrier.phrase}, cracks one, and learns from {helper.id} to slow down.",
        "Write a short lesson-learned tale with hens, morning light, one small mistake, and an ending image that proves the child changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    path = f["path_cfg"]
    carrier = f["carrier_cfg"]
    fix = f["fix_cfg"]
    load = f["load"]
    reasons = list(f.get("predicted_reasons", []))
    many = {2: "two", 4: "four", 6: "six"}[load]
    why = []
    if "too_many" in reasons:
        why.append(f"{many} eggs were too many for the {carrier.label}")
    if "hard_rattle" in reasons:
        why.append(f"{path.label} made the eggs knock about in the {carrier.label}")
    reason_text = " and ".join(why) if why else "the eggs were not being carried safely"
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was gathering eggs, and {helper.id}, who guided {hero.pronoun('object')} in the egg-dim morning.",
        ),
        (
            "What was the child trying to do?",
            f"{hero.id} wanted to carry {many} eggs from {place.label} in one quick trip. {hero.pronoun().capitalize()} was hurrying because helping with breakfast felt important.",
        ),
        (
            f"Why did an egg crack?",
            f"An egg cracked because {reason_text}. The problem was not meanness or magic; it came from a shaky way of carrying something fragile.",
        ),
        (
            f"What did {helper.id} teach {hero.id} after the crack?",
            f'{helper.id} told {hero.id} that gentle hands and gentle steps matter. Then {helper.pronoun()} gave {hero.pronoun("object")} {fix.phrase}, so the lesson turned into a safer second try.',
        ),
        (
            "How can you tell the child learned the lesson?",
            f'{hero.id} walked hush-hush on the second trip and did not rush again. The ending proves the change because the eggs arrived safely and {hero.pronoun()} said, "{f["lesson"]}"',
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["path_cfg"].tags) | set(f["fix_cfg"].tags) | {"careful"}
    tags |= set(f["carrier_cfg"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="coop",
        path="stones",
        carrier="tin_pail",
        load=4,
        hero_name="Pip",
        hero_gender="boy",
        helper_name="Nan",
        helper_type="grandmother",
        trait="hasty",
    ),
    StoryParams(
        place="barn_nest",
        path="boards",
        carrier="apron_fold",
        load=4,
        hero_name="Dot",
        hero_gender="girl",
        helper_name="Rose",
        helper_type="mother",
        trait="eager",
    ),
    StoryParams(
        place="garden_hutch",
        path="stones",
        carrier="apron_fold",
        load=6,
        hero_name="May",
        hero_gender="girl",
        helper_name="Jo",
        helper_type="grandfather",
        trait="bouncy",
    ),
    StoryParams(
        place="coop",
        path="boards",
        carrier="tin_pail",
        load=6,
        hero_name="Finn",
        hero_gender="boy",
        helper_name="Gran",
        helper_type="grandmother",
        trait="hasty",
    ),
    StoryParams(
        place="barn_nest",
        path="moss",
        carrier="apron_fold",
        load=4,
        hero_name="Nell",
        hero_gender="girl",
        helper_name="Mim",
        helper_type="mother",
        trait="careful",
    ),
]


ASP_RULES = r"""
risky(C, P, L) :- load_num(L, N), capacity(C, K), N > K.
risky(C, P, L) :- path(P), carrier(C), not padded(C), bump(P, B), stability(C, S), B > S.

safe(C, P, L) :- load_num(L, N), capacity(C, K), N <= K,
                 padded(C).
safe(C, P, L) :- load_num(L, N), capacity(C, K), N <= K,
                 bump(P, B), stability(C, S), B <= S.

has_fix(P, C0, L) :- carrier(C1), carrier(C0), C1 != C0, safe(C1, P, L).

valid(Place, P, C, L) :- affords(Place, P), risky(C, P, L), has_fix(P, C, L).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for path_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, path_id))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("bump", path_id, path.bump))
    for carrier_id, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", carrier_id))
        lines.append(asp.fact("capacity", carrier_id, carrier.capacity))
        lines.append(asp.fact("stability", carrier_id, carrier.stability))
        if carrier.padded:
            lines.append(asp.fact("padded", carrier_id))
    for load in LOAD_CHOICES:
        lines.append(asp.fact("load_choice", load))
        lines.append(asp.fact("load_num", load, load))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if "egg-dim" not in sample.story:
            raise StoryError('smoke test story is missing required word "egg-dim"')
        print("OK: smoke test story generation and emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation succeeded on seeds 0..9.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an egg-dim morning, a cracked egg, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--load", type=int, choices=LOAD_CHOICES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def _pick_helper_name(rng: random.Random) -> str:
    return rng.choice(HELPER_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    filtered = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.path is None or combo[1] == args.path)
        and (args.carrier is None or combo[2] == args.carrier)
        and (args.load is None or combo[3] == args.load)
    ]

    if args.place and args.path and args.path not in PLACES[args.place].affords:
        raise StoryError(
            explain_rejection(
                PLACES[args.place],
                PATHS[args.path],
                CARRIERS[args.carrier or next(iter(CARRIERS))],
                args.load if args.load is not None else LOAD_CHOICES[0],
            )
        )

    if args.carrier and args.path and args.load is not None:
        place_id = args.place or next(iter(PLACES))
        place = PLACES[place_id]
        if args.path in place.affords and not filtered:
            raise StoryError(explain_rejection(place, PATHS[args.path], CARRIERS[args.carrier], args.load))

    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, path_id, carrier_id, load = rng.choice(filtered)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    helper_name = args.helper_name or _pick_helper_name(rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        path=path_id,
        carrier=carrier_id,
        load=load,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.load not in LOAD_CHOICES:
        raise StoryError(f"(Unknown load: {params.load})")

    place = PLACES[params.place]
    path = PATHS[params.path]
    carrier = CARRIERS[params.carrier]

    if params.path not in place.affords or not risky(carrier, path, params.load) or best_fix(path, params.load, carrier) is None:
        raise StoryError(explain_rejection(place, path, carrier, params.load))

    world = tell(
        place=place,
        path=path,
        chosen_carrier=carrier,
        load=params.load,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, path, carrier, load) combos:\n")
        for place, path, carrier, load in combos:
            print(f"  {place:12} {path:7} {carrier:13} {load}")
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
            header = f"### {p.hero_name}: {p.carrier} with {p.load} eggs on {p.path} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
