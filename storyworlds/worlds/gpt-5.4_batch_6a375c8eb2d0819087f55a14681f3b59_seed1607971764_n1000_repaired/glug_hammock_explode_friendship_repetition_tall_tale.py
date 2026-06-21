#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/glug_hammock_explode_friendship_repetition_tall_tale.py
==================================================================================

A standalone story world for a tall-tale picnic about two friends, a mighty
hammock, and a barrel of fizzy drink that may explode if one friend keeps
pouring after the sensible stopping point.

Seed requirements rebuilt as world state
----------------------------------------
- words: "glug", "hammock", "explode"
- features: Friendship, Repetition
- style: Tall Tale

This world models a child-facing tall tale where:
- two friends string up an enormous hammock between huge trees,
- one friend keeps pouring fizzy drink into a corked picnic barrel,
- the repeated "glug, glug, glug" of the jug tempts another pour,
- the other friend predicts the danger and warns them,
- the story branches into a near-miss, a last-second save, or a sticky burst,
- the ending image proves what changed: the friends now share the drink in a
  safer way, and the hammock becomes a place for friendship rather than foolish
  boasting.

Run it
------
    python storyworlds/worlds/gpt-5.4/glug_hammock_explode_friendship_repetition_tall_tale.py
    python storyworlds/worlds/gpt-5.4/glug_hammock_explode_friendship_repetition_tall_tale.py --place riverbend --drink berry_fizz --vessel oak_barrel
    python storyworlds/worlds/gpt-5.4/glug_hammock_explode_friendship_repetition_tall_tale.py --vessel paper_cask
    python storyworlds/worlds/gpt-5.4/glug_hammock_explode_friendship_repetition_tall_tale.py --response sit_on_it
    python storyworlds/worlds/gpt-5.4/glug_hammock_explode_friendship_repetition_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/glug_hammock_explode_friendship_repetition_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/glug_hammock_explode_friendship_repetition_tall_tale.py --verify
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
BOLDNESS_INIT = 6.0
CALM_TRAITS = {"steady", "patient", "careful", "gentle"}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    giant_image: str
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
class Drink:
    id: str
    label: str
    phrase: str
    color: str
    base_fizz: int
    glug_line: str
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
class Vessel:
    id: str
    label: str
    phrase: str
    safe_fizz: int
    tough: bool = True
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
class HammockCfg:
    id: str
    label: str
    phrase: str
    patch: str
    comfy: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"pourer", "helper"}]

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


def _r_overpressure(world: World) -> list[str]:
    barrel = world.entities.get("barrel")
    if barrel is None:
        return []
    if barrel.meters["overpressure"] < THRESHOLD:
        return []
    sig = ("overpressure", barrel.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    barrel.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__danger__"]


def _r_sticky_sag(world: World) -> list[str]:
    hammock = world.entities.get("hammock")
    if hammock is None:
        return []
    if hammock.meters["sticky"] < THRESHOLD:
        return []
    sig = ("sticky_sag", hammock.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hammock.meters["sag"] += 1
    return ["__sag__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="overpressure", tag="physical", apply=_r_overpressure),
    Rule(name="sticky_sag", tag="physical", apply=_r_sticky_sag),
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


def valid_setup(drink: Drink, vessel: Vessel) -> bool:
    return drink.base_fizz <= vessel.safe_fizz


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def surge_level(drink: Drink, vessel: Vessel, extra_pours: int) -> int:
    return max(1, drink.base_fizz + extra_pours - vessel.safe_fizz + 1)


def is_contained(response: Response, drink: Drink, vessel: Vessel, extra_pours: int) -> bool:
    return response.power >= surge_level(drink, vessel, extra_pours)


def would_avert(bond: int, trait: str) -> bool:
    calm_bonus = 2 if trait in CALM_TRAITS else 0
    authority = bond + calm_bonus
    return authority > BOLDNESS_INIT + 2


def predict_burst(world: World, extra_pours: int) -> dict:
    sim = world.copy()
    barrel = sim.get("barrel")
    barrel.meters["overpressure"] = float(surge_level(
        sim.facts["drink_cfg"], sim.facts["vessel_cfg"], extra_pours
    ))
    propagate(sim, narrate=False)
    return {
        "danger": barrel.meters["danger"],
        "will_explode": True,
    }


def introduce(world: World, a: Entity, b: Entity, hammock_cfg: HammockCfg) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"In {world.place.label}, where {world.place.giant_image}, {a.id} and {b.id} "
        f"were the kind of friends who could stretch an afternoon till it felt as long as a summer."
    )
    world.say(
        f"Together they tied up {hammock_cfg.phrase} between two mighty trees. "
        f"The thing swung so wide and easy that folks said a whole flock of geese could have napped in it."
    )


def dream(world: World, a: Entity, b: Entity, drink: Drink) -> None:
    world.say(
        f"They planned to sip {drink.phrase} in the shade and trade stories until the clouds looked down to listen."
    )
    world.say(
        f'{a.id} patted the jug and grinned. "{drink.glug_line}"'
    )


def start_pour(world: World, a: Entity, drink: Drink, vessel: Vessel, hammock_cfg: HammockCfg) -> None:
    a.memes["boldness"] += 1
    world.say(
        f"{a.id} tipped the jug over {vessel.phrase} beside the {hammock_cfg.label}. "
        f"Out came the drink: glug, glug, glug, bright as {drink.color} sunshine and lively as hiccups in a horn."
    )
    world.say(
        f"The barrel liked the first pour well enough, so {a.id} decided it might like one more."
    )


def warn(world: World, helper: Entity, pourer: Entity, extra_pours: int, hammock_cfg: HammockCfg) -> None:
    pred = predict_burst(world, extra_pours)
    world.facts["predicted_danger"] = pred["danger"]
    helper.memes["care"] += 1
    extra = ""
    if helper.attrs.get("bond", 0) >= 8:
        extra = f" {helper.pronoun().capitalize()} knew {pourer.id} well enough to hear trouble before it happened."
    world.say(
        f'{helper.id} held up both hands. "{pourer.id}, if you keep pouring, that barrel will puff up and explode, '
        f'and the splash will slap our {hammock_cfg.label} clear crooked."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, drink: Drink, hammock_cfg: HammockCfg) -> None:
    a.memes["boldness"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} listened to {b.id}, set the jug down, and laughed at {a.pronoun("possessive")} own foolish hurry.'
    )
    world.say(
        f"Instead of cramming the drink into a corked barrel, they poured it into open tin cups and climbed into the {hammock_cfg.label} shoulder to shoulder."
    )
    world.say(
        f"The cups still said glug, glug, glug, but now it was a peaceful sound, fit for friends and shade."
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"One more glug never hurt a soul," {a.id} said, though {b.id} was already stepping closer with worried eyes.'
    )


def swell(world: World, drink: Drink, vessel: Vessel, extra_pours: int) -> None:
    barrel = world.get("barrel")
    barrel.meters["overpressure"] = float(surge_level(drink, vessel, extra_pours))
    propagate(world, narrate=False)
    world.say(
        f"So in went another pour: glug, glug, glug. At once the {vessel.label} swelled round as a toad in a thunderstorm and began to tremble in the grass."
    )


def rescue(world: World, helper: Entity, response: Response, vessel: Vessel) -> None:
    barrel = world.get("barrel")
    barrel.meters["overpressure"] = 0.0
    barrel.meters["danger"] = 0.0
    helper.memes["bravery"] += 1
    world.say(
        f"{helper.id} did not run. {helper.pronoun().capitalize()} {response.text.replace('{vessel}', vessel.label)}."
    )
    world.say(
        "The barrel gave one last grumble, then settled down as meek as a sleepy calf."
    )


def lesson_success(world: World, a: Entity, b: Entity, hammock_cfg: HammockCfg) -> None:
    for kid in (a, b):
        kid.memes["friendship"] += 1
        kid.memes["lesson"] += 1
        kid.memes["worry"] = 0.0
    world.say(
        f'{a.id} let out a long breath. "{b.id}, you saved our picnic," {a.pronoun()} said.'
    )
    world.say(
        f'{b.id} smiled and gave the {hammock_cfg.label} a pat. "A good friend is better than a loud idea," {b.pronoun()} said.'
    )


def explode(world: World, vessel: Vessel, drink: Drink, hammock_cfg: HammockCfg) -> None:
    barrel = world.get("barrel")
    hammock = world.get("hammock")
    barrel.meters["burst"] += 1
    hammock.meters["sticky"] += 1
    hammock.meters["tilted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the barrel had heard enough. It gave a round little hop and then did what {vessel.label}s sometimes do when pride gets pumped into them too fast: it did explode."
    )
    world.say(
        f"{drink.phrase.capitalize()} leapt into the air in a fizzy cloud and came raining down over the {hammock_cfg.label}, the grass, and both astonished friends."
    )


def rescue_fail(world: World, helper: Entity, response: Response, vessel: Vessel) -> None:
    helper.memes["bravery"] += 1
    world.say(
        f"{helper.id} {response.fail.replace('{vessel}', vessel.label)}, but the barrel was already too wild to listen."
    )


def clean_together(world: World, a: Entity, b: Entity, hammock_cfg: HammockCfg) -> None:
    hammock = world.get("hammock")
    hammock.meters["sticky"] = 0.0
    hammock.meters["sag"] = 0.0
    hammock.meters["tilted"] = 0.0
    hammock.meters["patched"] += 1
    for kid in (a, b):
        kid.memes["friendship"] += 2
        kid.memes["lesson"] += 1
        kid.memes["worry"] = 0.0
    world.say(
        f"For one blink nobody spoke. Then {a.id} grabbed a bucket of creek water, {b.id} fetched {hammock_cfg.patch}, and they set to work together."
    )
    world.say(
        f"They scrubbed, laughed, retied the knots, and patched the {hammock_cfg.label} until it hung straight again, sticky no more."
    )
    world.say(
        f'After that, they poured the rest of the drink into open cups. "From now on," {a.id} said, "we listen before things get big enough to boom."'
    )


def ending_image(world: World, a: Entity, b: Entity, hammock_cfg: HammockCfg, drink: Drink, outcome: str) -> None:
    if outcome == "averted":
        world.say(
            f"By sunset the two friends were rocking in the {hammock_cfg.label}, passing cups of {drink.label} back and forth and grinning at how fine a quiet glug could sound."
        )
    elif outcome == "contained":
        world.say(
            f"Before long they were lying in the {hammock_cfg.label}, sharing {drink.label} from cups instead of daring the barrel again, and the evening felt bigger for being wiser."
        )
    else:
        world.say(
            f"When the sun slid low, the friends were already back in the mended {hammock_cfg.label}, shoulders touching, sipping what little drink remained and guarding it with common sense."
        )


def tell(
    place: Place,
    drink: Drink,
    vessel: Vessel,
    hammock_cfg: HammockCfg,
    response: Response,
    *,
    pourer_name: str = "Tess",
    pourer_gender: str = "girl",
    helper_name: str = "Bo",
    helper_gender: str = "boy",
    helper_trait: str = "steady",
    bond: int = 8,
    extra_pours: int = 1,
) -> World:
    world = World(place)
    a = world.add(Entity(
        id=pourer_name,
        kind="character",
        type=pourer_gender,
        role="pourer",
        traits=["bold"],
        attrs={"bond": bond},
    ))
    b = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[helper_trait],
        attrs={"bond": bond},
    ))
    hammock = world.add(Entity(
        id="hammock",
        type="hammock",
        label=hammock_cfg.label,
        attrs={"patch": hammock_cfg.patch},
    ))
    barrel = world.add(Entity(
        id="barrel",
        type="barrel",
        label=vessel.label,
    ))

    for ent in (a, b, hammock, barrel):
        ent.meters["overpressure"] = 0.0
        ent.meters["danger"] = 0.0
        ent.meters["sticky"] = 0.0
        ent.meters["sag"] = 0.0
        ent.meters["tilted"] = 0.0
        ent.meters["burst"] = 0.0
        ent.meters["patched"] = 0.0
        ent.memes["worry"] = 0.0
        ent.memes["friendship"] = 0.0
        ent.memes["lesson"] = 0.0
        ent.memes["boldness"] = 0.0
        ent.memes["defiance"] = 0.0
        ent.memes["relief"] = 0.0
        ent.memes["care"] = 0.0
        ent.memes["joy"] = 0.0
        ent.memes["bravery"] = 0.0

    world.facts.update(
        place=place,
        drink_cfg=drink,
        vessel_cfg=vessel,
        hammock_cfg=hammock_cfg,
        response=response,
        extra_pours=extra_pours,
    )

    introduce(world, a, b, hammock_cfg)
    dream(world, a, b, drink)

    world.para()
    start_pour(world, a, drink, vessel, hammock_cfg)
    warn(world, b, a, extra_pours, hammock_cfg)

    averted = would_avert(bond, helper_trait)

    if averted:
        back_down(world, a, b, drink, hammock_cfg)
        outcome = "averted"
        contained = True
    else:
        defy(world, a, b)
        world.para()
        swell(world, drink, vessel, extra_pours)
        contained = is_contained(response, drink, vessel, extra_pours)
        world.para()
        if contained:
            rescue(world, b, response, vessel)
            lesson_success(world, a, b, hammock_cfg)
            outcome = "contained"
        else:
            rescue_fail(world, b, response, vessel)
            explode(world, vessel, drink, hammock_cfg)
            clean_together(world, a, b, hammock_cfg)
            outcome = "exploded"

    world.para()
    ending_image(world, a, b, hammock_cfg, drink, outcome)

    world.facts.update(
        pourer=a,
        helper=b,
        hammock=hammock,
        barrel=barrel,
        outcome=outcome,
        averted=averted,
        contained=contained,
        exploded=barrel.meters["burst"] >= THRESHOLD,
        bond=bond,
        helper_trait=helper_trait,
        surge=surge_level(drink, vessel, extra_pours),
    )
    return world


PLACES = {
    "riverbend": Place(
        id="riverbend",
        label="the river bend",
        giant_image="the cottonwoods were so tall they seemed to comb the sky",
        affords={"berry_fizz", "apple_pop"},
        tags={"river", "trees"},
    ),
    "prairie": Place(
        id="prairie",
        label="the windy prairie",
        giant_image="the grass rolled in waves big enough to hide a wagon",
        affords={"apple_pop", "peach_sparkle"},
        tags={"prairie", "wind"},
    ),
    "canyon": Place(
        id="canyon",
        label="the red canyon",
        giant_image="the cliff walls threw back every laugh until it sounded twice as grand",
        affords={"berry_fizz", "peach_sparkle"},
        tags={"canyon", "echo"},
    ),
}

DRINKS = {
    "berry_fizz": Drink(
        id="berry_fizz",
        label="berry fizz",
        phrase="a jug of berry fizz",
        color="purple",
        base_fizz=2,
        glug_line='"Listen to that glug, glug, glug,"',
        tags={"fizz", "berries"},
    ),
    "apple_pop": Drink(
        id="apple_pop",
        label="apple pop",
        phrase="a crock of apple pop",
        color="gold",
        base_fizz=1,
        glug_line='"Hear that glug, glug, glug,"',
        tags={"fizz", "apples"},
    ),
    "peach_sparkle": Drink(
        id="peach_sparkle",
        label="peach sparkle",
        phrase="a jug of peach sparkle",
        color="pink",
        base_fizz=2,
        glug_line='"That is the sweetest glug, glug, glug in three counties,"',
        tags={"fizz", "peaches"},
    ),
}

VESSELS = {
    "oak_barrel": Vessel(
        id="oak_barrel",
        label="oak barrel",
        phrase="an oak barrel",
        safe_fizz=2,
        tough=True,
        tags={"barrel", "wood"},
    ),
    "copper_keg": Vessel(
        id="copper_keg",
        label="copper keg",
        phrase="a copper keg",
        safe_fizz=3,
        tough=True,
        tags={"keg", "metal"},
    ),
    "paper_cask": Vessel(
        id="paper_cask",
        label="paper cask",
        phrase="a paper cask",
        safe_fizz=0,
        tough=False,
        tags={"cask"},
    ),
}

HAMMOCKS = {
    "rope": HammockCfg(
        id="rope",
        label="hammock",
        phrase="a long rope hammock",
        patch="a square of sailcloth",
        comfy="deep as a nest",
        tags={"hammock", "rope"},
    ),
    "quilt": HammockCfg(
        id="quilt",
        label="hammock",
        phrase="a quilted hammock",
        patch="a stout blue patch",
        comfy="soft as a cloud",
        tags={"hammock", "cloth"},
    ),
    "sailcloth": HammockCfg(
        id="sailcloth",
        label="hammock",
        phrase="a broad sailcloth hammock",
        patch="a bright red patch",
        comfy="wide as a porch swing",
        tags={"hammock", "sailcloth"},
    ),
}

RESPONSES = {
    "vent_spout": Response(
        id="vent_spout",
        sense=3,
        power=3,
        text="snapped open the little vent spout on the {vessel} and let the angry fizz hiss itself calm",
        fail="snapped open the vent spout on the {vessel}",
        qa_text="opened the vent spout so the extra fizz could escape",
        tags={"vent", "fizz"},
    ),
    "ease_cork": Response(
        id="ease_cork",
        sense=2,
        power=2,
        text="eased the cork on the {vessel} just enough to let the pressure whistle out",
        fail="eased the cork on the {vessel}",
        qa_text="eased the cork and let the pressure whistle out",
        tags={"cork", "fizz"},
    ),
    "sit_on_it": Response(
        id="sit_on_it",
        sense=1,
        power=1,
        text="plopped down on the {vessel} and somehow held it still",
        fail="tried to sit on the {vessel}",
        qa_text="sat on the barrel",
        tags={"barrel"},
    ),
}

GIRL_NAMES = ["Tess", "Molly", "June", "Ivy", "Ada", "Ruth", "Clara", "Elsie"]
BOY_NAMES = ["Bo", "Wade", "Jeb", "Finn", "Eli", "Ned", "Cal", "Roy"]
TRAITS = ["steady", "patient", "careful", "gentle", "quick", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for drink_id in sorted(place.affords):
            drink = DRINKS[drink_id]
            for vessel_id, vessel in VESSELS.items():
                if valid_setup(drink, vessel):
                    combos.append((place_id, drink_id, vessel_id))
    return combos


@dataclass
class StoryParams:
    place: str
    drink: str
    vessel: str
    hammock: str
    response: str
    pourer_name: str
    pourer_gender: str
    helper_name: str
    helper_gender: str
    helper_trait: str
    bond: int = 8
    extra_pours: int = 1
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
    "hammock": [
        (
            "What is a hammock?",
            "A hammock is a hanging bed made of cloth or rope. You tie it between two strong supports so it can swing."
        )
    ],
    "fizz": [
        (
            "Why can fizzy drinks push on a closed container?",
            "Fizzy drinks hold tiny bubbles of gas. In a closed container those bubbles push outward, so too much pressure can build up."
        )
    ],
    "vent": [
        (
            "What does a vent do on a barrel or bottle?",
            "A vent gives trapped air or gas a safe way out. Letting pressure escape can keep a container from popping."
        )
    ],
    "cork": [
        (
            "Why might someone loosen a cork carefully?",
            "Loosening a cork a little can let built-up pressure out slowly. Doing it gently is safer than yanking it hard."
        )
    ],
    "patch": [
        (
            "What is a patch for?",
            "A patch covers a weak or torn spot and helps hold cloth together again. People use patches to mend things instead of throwing them away."
        )
    ],
    "friendship": [
        (
            "What does a good friend do when trouble is coming?",
            "A good friend warns you, helps you, and stays with you while you fix the mess. Friendship is not just fun; it is also care and honesty."
        )
    ],
}
KNOWLEDGE_ORDER = ["hammock", "fizz", "vent", "cork", "patch", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["pourer"]
    b = f["helper"]
    drink = f["drink_cfg"]
    vessel = f["vessel_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a tall tale for a young child that includes the word "glug" and a giant hammock, where two friends stop a fizzy mistake before anything can explode.',
            f"Tell a friendship story where {a.id} keeps hearing glug, glug, glug and wants one more pour, but {b.id} talks {a.pronoun('object')} into the safer plan.",
            f'Write a playful tall tale with repetition, a hammock, and a near-miss ending where the friends choose cups over a corked barrel.',
        ]
    if outcome == "contained":
        return [
            f'Write a tall tale for a young child that includes "glug", "hammock", and "explode", but the friends stop the fizzy danger just in time.',
            f"Tell a story where {a.id} overdoes the pouring, {b.id} acts fast, and friendship saves the picnic.",
            f'Write a repetitive, child-facing tall tale where glug, glug, glug leads to danger, but a clever friend keeps the barrel from bursting.',
        ]
    return [
        f'Write a tall tale for a young child using the words "glug", "hammock", and "explode", where two friends make a fizzy mess and then fix it together.',
        f"Tell a friendship story where a giant picnic nearly goes wrong because one friend ignores a warning and the barrel does explode.",
        f'Write a tall tale with repetition and a sticky ending that becomes happy again because the friends mend the hammock together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["pourer"]
    b = f["helper"]
    drink = f["drink_cfg"]
    vessel = f["vessel_cfg"]
    hammock_cfg = f["hammock_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}. They set up a giant {hammock_cfg.label} and planned to share {drink.label} together."
        ),
        (
            "Why did the story keep saying glug, glug, glug?",
            f"The repeated glug, glug, glug was the sound of the fizzy drink being poured. It mattered because that tempting sound made {a.id} want to keep adding more."
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned {a.id} because the closed {vessel.label} was getting too full of fizzy pressure. {b.pronoun().capitalize()} knew the barrel could explode and splash the {hammock_cfg.label}."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What changed after {a.id} listened?",
            f"{a.id} stopped trying to fill the closed barrel and switched to open cups instead. That kept the picnic calm and protected the hammock."
        ))
        qa.append((
            "How did friendship matter in the ending?",
            f"Friendship mattered because {b.id} told the truth and {a.id} chose to listen. The safe ending happened because the friends trusted each other more than the foolish idea."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"How did {b.id} stop the danger?",
            f"{b.id} {response.qa_text.replace('{target}', vessel.label).replace('{vessel}', vessel.label)}. That let the pressure out before the {vessel.label} could burst."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the friends safe in the hammock, sharing the drink from cups. The ending proves they learned to enjoy the picnic without daring the barrel again."
        ))
    else:
        qa.append((
            f"What happened when the barrel did explode?",
            f"The fizzy drink burst up into the air and splashed over the hammock and both friends. The hammock sagged and turned sticky because the pressure had grown too big."
        ))
        qa.append((
            "How did the friends fix the problem?",
            f"They worked together to scrub, patch, and retie the hammock. The second part matters because the mess did not end the friendship; it gave them a chance to repair things together."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"hammock", "fizz", "friendship"}
    if f["response"].id == "vent_spout":
        tags.add("vent")
    if f["response"].id == "ease_cork":
        tags.add("cork")
    if f["outcome"] == "exploded":
        tags.add("patch")
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
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="riverbend",
        drink="berry_fizz",
        vessel="oak_barrel",
        hammock="rope",
        response="vent_spout",
        pourer_name="Tess",
        pourer_gender="girl",
        helper_name="Bo",
        helper_gender="boy",
        helper_trait="steady",
        bond=9,
        extra_pours=1,
    ),
    StoryParams(
        place="prairie",
        drink="apple_pop",
        vessel="oak_barrel",
        hammock="quilt",
        response="ease_cork",
        pourer_name="Wade",
        pourer_gender="boy",
        helper_name="June",
        helper_gender="girl",
        helper_trait="thoughtful",
        bond=7,
        extra_pours=2,
    ),
    StoryParams(
        place="canyon",
        drink="peach_sparkle",
        vessel="copper_keg",
        hammock="sailcloth",
        response="ease_cork",
        pourer_name="Ada",
        pourer_gender="girl",
        helper_name="Cal",
        helper_gender="boy",
        helper_trait="quick",
        bond=5,
        extra_pours=3,
    ),
    StoryParams(
        place="riverbend",
        drink="apple_pop",
        vessel="copper_keg",
        hammock="rope",
        response="vent_spout",
        pourer_name="Molly",
        pourer_gender="girl",
        helper_name="Eli",
        helper_gender="boy",
        helper_trait="patient",
        bond=10,
        extra_pours=0,
    ),
]


def explain_rejection(drink: Drink, vessel: Vessel) -> str:
    return (
        f"(No story: {drink.label} is fizzier than a {vessel.label} can reasonably hold. "
        f"The picnic barrel would be a bad setup before the tale even began. "
        f"Pick a tougher vessel like an oak barrel or copper keg.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer choice such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.bond, params.helper_trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], DRINKS[params.drink], VESSELS[params.vessel], params.extra_pours)
    return "contained" if contained else "exploded"


ASP_RULES = r"""
% --- gate ---------------------------------------------------------------
valid_setup(D, V) :- drink(D), vessel(V), base_fizz(D, F), safe_fizz(V, S), F <= S.
valid(P, D, V) :- place(P), affords(P, D), valid_setup(D, V).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% --- outcome model ------------------------------------------------------
calm_trait(T) :- trait(T), calm(T).
calm_bonus(2) :- calm_trait(_).
calm_bonus(0) :- not calm_trait(_).
authority(B + C) :- bond(B), calm_bonus(C).
averted :- authority(A), boldness_init(B), A > B + 2.

surge(F + E - S + 1) :- chosen_drink(D), chosen_vessel(V), base_fizz(D, F), safe_fizz(V, S), extra_pours(E), valid_setup(D, V).
contained :- chosen_response(R), power(R, P), surge(G), P >= G.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(exploded) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for drink_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, drink_id))
    for drink_id, drink in DRINKS.items():
        lines.append(asp.fact("drink", drink_id))
        lines.append(asp.fact("base_fizz", drink_id, drink.base_fizz))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        lines.append(asp.fact("safe_fizz", vessel_id, vessel.safe_fizz))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("calm", trait))
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
        asp.fact("chosen_drink", params.drink),
        asp.fact("chosen_vessel", params.vessel),
        asp.fact("chosen_response", params.response),
        asp.fact("extra_pours", params.extra_pours),
        asp.fact("bond", params.bond),
        asp.fact("trait", params.helper_trait),
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
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(120):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: two friends, a giant hammock, and a fizzy barrel that may explode."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--hammock", choices=HAMMOCKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--extra-pours", type=int, choices=[0, 1, 2, 3], dest="extra_pours")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_person(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.drink and args.vessel:
        drink = DRINKS[args.drink]
        vessel = VESSELS[args.vessel]
        if not valid_setup(drink, vessel):
            raise StoryError(explain_rejection(drink, vessel))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.drink is None or c[1] == args.drink)
        and (args.vessel is None or c[2] == args.vessel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, drink, vessel = rng.choice(sorted(combos))
    hammock = args.hammock or rng.choice(sorted(HAMMOCKS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    pourer_name, pourer_gender = _pick_person(rng)
    helper_name, helper_gender = _pick_person(rng, avoid=pourer_name)
    helper_trait = rng.choice(TRAITS)
    bond = rng.randint(4, 10)
    extra_pours = args.extra_pours if args.extra_pours is not None else rng.randint(0, 3)

    return StoryParams(
        place=place,
        drink=drink,
        vessel=vessel,
        hammock=hammock,
        response=response,
        pourer_name=pourer_name,
        pourer_gender=pourer_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        bond=bond,
        extra_pours=extra_pours,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.drink not in DRINKS:
        raise StoryError(f"(Unknown drink: {params.drink})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.hammock not in HAMMOCKS:
        raise StoryError(f"(Unknown hammock: {params.hammock})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not valid_setup(DRINKS[params.drink], VESSELS[params.vessel]):
        raise StoryError(explain_rejection(DRINKS[params.drink], VESSELS[params.vessel]))

    world = tell(
        PLACES[params.place],
        DRINKS[params.drink],
        VESSELS[params.vessel],
        HAMMOCKS[params.hammock],
        RESPONSES[params.response],
        pourer_name=params.pourer_name,
        pourer_gender=params.pourer_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        bond=params.bond,
        extra_pours=params.extra_pours,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, drink, vessel) combos:\n")
        for place, drink, vessel in combos:
            print(f"  {place:10} {drink:14} {vessel}")
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
                f"### {p.pourer_name} & {p.helper_name}: {p.drink} in {p.vessel} "
                f"at {p.place} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
