#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hollyhock_dialogue_foreshadowing_misunderstanding_tall_tale.py
==========================================================================================

A standalone story world about a child, a giant hollyhock, and a silly town
misunderstanding told in a tall-tale style. The world model tracks a fast-growing
flower, wind strain, a distant watcher who mistakes the plant for something much
larger, and whether a sensible support is tied on in time.

The domain is built to support:
- Dialogue: the story runs on spoken boasts, warnings, and corrections.
- Foreshadowing: a grounded prediction beat warns that anything growing this tall
  will need tying before the wind gets ideas.
- Misunderstanding: a faraway watcher mistakes the towering hollyhock for some
  giant object and spreads alarm before the truth is seen.

Run it
------
    python storyworlds/worlds/gpt-5.4/hollyhock_dialogue_foreshadowing_misunderstanding_tall_tale.py
    python storyworlds/worlds/gpt-5.4/hollyhock_dialogue_foreshadowing_misunderstanding_tall_tale.py --place riverside --watcher ferryman
    python storyworlds/worlds/gpt-5.4/hollyhock_dialogue_foreshadowing_misunderstanding_tall_tale.py --support thread
    python storyworlds/worlds/gpt-5.4/hollyhock_dialogue_foreshadowing_misunderstanding_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/hollyhock_dialogue_foreshadowing_misunderstanding_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/hollyhock_dialogue_foreshadowing_misunderstanding_tall_tale.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"                 # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man", "ferryman", "baker"}
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
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
    landmark: str
    soil: int
    wind: int
    affords: set[str] = field(default_factory=set)
    watchers: set[str] = field(default_factory=set)
    closing: str = ""
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
class Booster:
    id: str
    label: str
    phrase: str
    boost: int
    brag: str
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
class WatcherCfg:
    id: str
    type: str
    label: str
    view: str
    mistake: str
    cry: str
    settle: str
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
class Support:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    success: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World + rules
# ---------------------------------------------------------------------------
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


def _r_visible(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["height"] < 5:
        return out
    sig = ("visible", plant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["visible"] += 1
    world.get("hero").memes["wonder"] += 1
    out.append("__visible__")
    return out


def _r_lean(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["height"] < 5:
        return out
    if plant.attrs.get("supported"):
        return out
    if world.facts.get("wind_now", 0) <= 0:
        return out
    sig = ("lean", plant.id, world.facts.get("wind_now", 0))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["lean"] += world.facts["wind_now"]
    world.get("helper").memes["worry"] += 1
    out.append("__lean__")
    return out


def _r_misunderstand(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    watcher = world.get("watcher")
    if plant.meters["visible"] < THRESHOLD:
        return out
    if plant.meters["lean"] < THRESHOLD:
        return out
    sig = ("mistake", watcher.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    watcher.memes["alarm"] += 1
    world.get("hero").memes["confusion"] += 1
    out.append("__mistake__")
    return out


def _r_snap(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.attrs.get("supported"):
        return out
    strain = world.facts.get("strain", 0)
    if strain < 8:
        return out
    sig = ("snap", plant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["snapped"] += 1
    world.get("hero").memes["sadness"] += 1
    world.get("helper").memes["worry"] += 1
    out.append("__snap__")
    return out


CAUSAL_RULES = [
    Rule(name="visible", tag="physical", apply=_r_visible),
    Rule(name="lean", tag="physical", apply=_r_lean),
    Rule(name="misunderstand", tag="social", apply=_r_misunderstand),
    Rule(name="snap", tag="physical", apply=_r_snap),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def giant_enough(place: Place, booster: Booster) -> bool:
    return place.soil + booster.boost >= 5


def watcher_plausible(place: Place, watcher: WatcherCfg) -> bool:
    return watcher.id in place.watchers


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for booster_id, booster in BOOSTERS.items():
            if not giant_enough(place, booster):
                continue
            for watcher_id, watcher in WATCHERS.items():
                if watcher_plausible(place, watcher):
                    combos.append((place_id, booster_id, watcher_id))
    return combos


def sensible_supports() -> list[Support]:
    return [s for s in SUPPORTS.values() if s.sense >= SENSE_MIN]


def growth_height(place: Place, booster: Booster) -> int:
    return place.soil + booster.boost + 2


def strain_of(place: Place, booster: Booster, delay: int) -> int:
    return place.wind + growth_height(place, booster) + delay


def is_saved(place: Place, booster: Booster, support: Support, delay: int) -> bool:
    return support.power >= strain_of(place, booster, delay)


def explain_place_booster(place: Place, booster: Booster) -> str:
    return (
        f"(No story: {booster.label} would help, but in {place.label} the soil is "
        f"not rich enough for a hollyhock tall enough to cause the big misunderstanding. "
        f"Pick a richer place or a stronger booster.)"
    )


def explain_watcher(place: Place, watcher: WatcherCfg) -> str:
    return (
        f"(No story: a {watcher.label} does not have the right far-off view in "
        f"{place.label} to mistake the hollyhock for {watcher.mistake}. "
        f"Pick a watcher whose viewpoint fits that place.)"
    )


def explain_support(support_id: str) -> str:
    support = SUPPORTS[support_id]
    better = ", ".join(sorted(s.id for s in sensible_supports()))
    return (
        f"(Refusing support '{support_id}': it scores too low on common sense "
        f"(sense={support.sense} < {SENSE_MIN}). A giant hollyhock needs a real tie, "
        f"not a flimsy one. Try: {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction helpers
# ---------------------------------------------------------------------------
def predict_trouble(world: World) -> dict:
    sim = world.copy()
    place = sim.facts["place_cfg"]
    booster = sim.facts["booster_cfg"]
    plant = sim.get("plant")
    plant.meters["height"] = float(growth_height(place, booster))
    sim.facts["wind_now"] = place.wind
    sim.facts["strain"] = strain_of(place, booster, sim.facts["delay"])
    propagate(sim, narrate=False)
    return {
        "visible": plant.meters["visible"] >= THRESHOLD,
        "lean": plant.meters["lean"],
        "mistake": sim.get("watcher").memes["alarm"] >= THRESHOLD,
        "strain": sim.facts["strain"],
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {place.label}, where {place.landmark}, {hero.id} helped "
        f"{helper.label_word} plant a hollyhock seed beside the fence."
    )
    world.say(
        f'"That little seed is polite now," said {helper.id}, '
        f'"but give it a drink and it may grow so tall it has to duck for clouds."'
    )


def feed(world: World, hero: Entity, booster: Booster) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} carried {booster.phrase} in both hands and poured it at the "
        f"roots as carefully as if feeding a baby bird."
    )
    world.say(
        f'"There," {hero.pronoun()} said. "Drink up, hollyhock."'
    )
    world.say(
        f'{booster.brag}'
    )


def foreshadow(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_strain"] = pred["strain"]
    if pred["visible"] and pred["lean"] >= THRESHOLD:
        helper.memes["worry"] += 1
        world.say(
            f"A breeze came sauntering through {place.label} and gave the tiny leaves "
            f"a practice tug, as if the wind were measuring them for trouble."
        )
        world.say(
            f'"Hear that?" said {helper.id}. "If this hollyhock means to grow as high '
            f'as my stories, we had better tie it before sunset. Tall things love to lean."'
        )
    else:
        world.say(
            f"The afternoon wind brushed the leaves, but {helper.id} only smiled and said, "
            f'"A growing hollyhock always keeps one surprise in its pocket."'
        )


def overnight_growth(world: World, hero: Entity, place: Place, booster: Booster) -> None:
    plant = world.get("plant")
    plant.meters["height"] = float(growth_height(place, booster))
    world.facts["wind_now"] = place.wind
    world.facts["strain"] = strain_of(place, booster, world.facts["delay"])
    propagate(world, narrate=False)
    hero.memes["wonder"] += 1
    world.say(
        f"By morning the hollyhock had shot up past the fence, past the shed, and nearly "
        f"up to {place.landmark}."
    )
    world.say(
        f"It stood so tall that sparrows paused halfway up to rest and gossip."
    )
    if world.get("plant").meters["lean"] >= THRESHOLD:
        world.say(
            f"But the wind had started nudging the long green stalk sideways, little by little."
        )


def misunderstanding(world: World, watcher: Entity, watcher_cfg: WatcherCfg) -> None:
    propagate(world, narrate=False)
    if watcher.memes["alarm"] >= THRESHOLD:
        world.say(
            f"From {watcher_cfg.view}, {watcher.id} squinted at the leaning shape and gasped."
        )
        world.say(
            f'"{watcher_cfg.cry}" {watcher.pronoun()} shouted.'
        )
        world.say(
            f"In less than a minute, half the town was peeking over hats and aprons, certain "
            f"they were about to meet {watcher_cfg.mistake}."
        )


def run_to_flower(world: World, hero: Entity, helper: Entity, watcher: Entity) -> None:
    hero.memes["confusion"] += 1
    world.say(
        f'"That is not a giant anything," cried {hero.id}. "{helper.id} and I planted that hollyhock!"'
    )
    world.say(
        f"{hero.id}, {helper.id}, and {watcher.id} hurried to the fence to see whether the stalk "
        f"could be steadied in time."
    )


def tie_support(world: World, helper: Entity, support: Support) -> None:
    plant = world.get("plant")
    plant.attrs["supported"] = True
    plant.meters["lean"] = 0.0
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} {support.success}."
    )


def bloom_finish(world: World, hero: Entity, watcher: Entity, watcher_cfg: WatcherCfg, place: Place) -> None:
    plant = world.get("plant")
    plant.meters["bloomed"] += 1
    hero.memes["joy"] += 1
    watcher.memes["relief"] += 1
    world.say(
        f"At the top, a blossom opened wide as a supper plate, pink as sunrise, and plain as truth."
    )
    world.say(
        f'{watcher.id} laughed until {watcher.pronoun("possessive")} shoulders shook. '
        f'"{watcher_cfg.settle}," {watcher.pronoun()} said.'
    )
    world.say(
        f"After that, nobody in {place.label} pointed at the hollyhock with fear. They pointed with pride."
    )


def snap_fail(world: World, hero: Entity, helper: Entity, support: Support) -> None:
    plant = world.get("plant")
    plant.meters["snapped"] = 1.0
    hero.memes["sadness"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} {support.fail}."
    )
    world.say(
        f"The great stalk bowed once, twice, and then snapped with a sound like a broomstick breaking over a giant's knee."
    )


def seed_resolution(world: World, hero: Entity, watcher: Entity, watcher_cfg: WatcherCfg, place: Place) -> None:
    plant = world.get("plant")
    plant.meters["seeded"] += 1
    hero.memes["hope"] += 1
    watcher.memes["relief"] += 1
    world.say(
        f"The flower head landed softly in a wheelbarrow and spilled a shower of black seeds as neat as coins."
    )
    world.say(
        f'"Well," said {watcher.id}, staring at them, "{watcher_cfg.settle} Next year we may need a longer fence."'
    )
    world.say(
        f"By evening, {hero.id} was already pressing the seeds into new rows of earth, and the whole town was asking for one."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    booster: Booster,
    watcher_cfg: WatcherCfg,
    support: Support,
    *,
    hero_name: str = "Molly",
    hero_type: str = "girl",
    helper_name: str = "Grandma June",
    helper_type: str = "grandmother",
    delay: int = 0,
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["eager"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        traits=["boastful", "kind"],
    ))
    watcher = world.add(Entity(
        id=watcher_cfg.label.title(),
        kind="character",
        type=watcher_cfg.type,
        label=watcher_cfg.label,
        role="watcher",
        traits=["far-seeing"],
    ))
    plant = world.add(Entity(
        id="plant",
        kind="thing",
        type="flower",
        label="hollyhock",
        role="plant",
        attrs={"supported": False},
    ))

    world.facts.update(
        place_cfg=place,
        booster_cfg=booster,
        watcher_cfg=watcher_cfg,
        support_cfg=support,
        delay=delay,
    )

    introduce(world, hero, helper, place)
    feed(world, hero, booster)

    world.para()
    foreshadow(world, hero, helper, place)

    world.para()
    overnight_growth(world, hero, place, booster)
    misunderstanding(world, watcher, watcher_cfg)
    run_to_flower(world, hero, helper, watcher)

    world.para()
    saved = is_saved(place, booster, support, delay)
    if saved:
        tie_support(world, helper, support)
        bloom_finish(world, hero, watcher, watcher_cfg, place)
        outcome = "saved"
    else:
        snap_fail(world, hero, helper, support)
        seed_resolution(world, hero, watcher, watcher_cfg, place)
        outcome = "snapped"

    world.facts.update(
        hero=hero,
        helper=helper,
        watcher=watcher,
        plant=plant,
        visible=plant.meters["visible"] >= THRESHOLD,
        misunderstood=watcher.memes["alarm"] >= THRESHOLD,
        outcome=outcome,
        saved=saved,
        strain=world.facts["strain"],
        promised_warning=world.facts.get("predicted_strain", 0) > 0,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "farmyard": Place(
        id="farmyard",
        label="the farmyard",
        landmark="the red barn wore its rooster vane like a hat",
        soil=3,
        wind=2,
        affords={"rain_barrel", "compost_tea"},
        watchers={"baker", "hill_shepherd"},
        closing="the bloom bobbed above the barn roof",
        tags={"yard"},
    ),
    "riverside": Place(
        id="riverside",
        label="the riverside lane",
        landmark="the ferry rope stretched across the water like a line on a blue sleeve",
        soil=2,
        wind=3,
        affords={"river_silt", "rain_barrel"},
        watchers={"ferryman", "baker"},
        closing="the bloom shone over the river",
        tags={"river"},
    ),
    "millhill": Place(
        id="millhill",
        label="the mill hill",
        landmark="the windmill lifted its arms all day and never got tired",
        soil=3,
        wind=3,
        affords={"compost_tea", "river_silt"},
        watchers={"hill_shepherd", "ferryman"},
        closing="the bloom nodded above the mill sails",
        tags={"hill"},
    ),
}

BOOSTERS = {
    "rain_barrel": Booster(
        id="rain_barrel",
        label="rain-barrel water",
        phrase="a dipper of rain-barrel water",
        boost=2,
        brag='"That ought to put springs in its shoes," said the helper.',
        tags={"water", "garden"},
    ),
    "compost_tea": Booster(
        id="compost_tea",
        label="compost tea",
        phrase="a warm pail of compost tea",
        boost=3,
        brag='"Now that is strong enough to make a fencepost think about blooming," said the helper.',
        tags={"garden", "soil"},
    ),
    "river_silt": Booster(
        id="river_silt",
        label="river silt",
        phrase="a bucket of rich river silt and water",
        boost=3,
        brag='"River mud grows ideas as well as flowers," said the helper.',
        tags={"river", "soil"},
    ),
}

WATCHERS = {
    "ferryman": WatcherCfg(
        id="ferryman",
        type="ferryman",
        label="the ferryman",
        view="midstream on the ferry",
        mistake="a giant fishing pole",
        cry="There is a giant on the bank, and he has dropped his fishing pole!",
        settle="I declare, that giant has turned into a flower",
        tags={"ferry", "misunderstanding"},
    ),
    "baker": WatcherCfg(
        id="baker",
        type="baker",
        label="the baker",
        view="behind the bakery chimney smoke",
        mistake="a giant feather",
        cry="Mercy me, a giant has lost a feather bigger than my bread paddle!",
        settle="I thought it was a giant feather, but it is only the tallest hollyhock I ever saw",
        tags={"bakery", "misunderstanding"},
    ),
    "hill_shepherd": WatcherCfg(
        id="hill_shepherd",
        type="man",
        label="the shepherd",
        view="up on the windy hill",
        mistake="a giant flagpole",
        cry="Sound the bell! Some giant has planted a flagpole by the houses!",
        settle="That is no flagpole at all; it is a hollyhock with ideas above its station",
        tags={"hill", "misunderstanding"},
    ),
}

SUPPORTS = {
    "stake": Support(
        id="stake",
        label="oak stake",
        phrase="an oak stake and soft cloth ties",
        sense=3,
        power=10,
        success="drove in an oak stake, looped soft cloth around the hollyhock, and tied it snug and straight",
        fail="tried to brace the stalk with an oak stake, but the wind had already taught it too much wobbling",
        qa_text="used an oak stake and soft ties to hold the hollyhock upright",
        tags={"stake", "support"},
    ),
    "wagon_rope": Support(
        id="wagon_rope",
        label="wagon rope",
        phrase="a wagon rope tied to the fence",
        sense=3,
        power=9,
        success="threw a wagon rope around the stalk and tied it to the fence until it stood as steady as a schoolmaster",
        fail="snatched a wagon rope and tried to tie the stalk to the fence, but the long stem had bent too far already",
        qa_text="tied the hollyhock to the fence with a wagon rope",
        tags={"rope", "support"},
    ),
    "clothesline": Support(
        id="clothesline",
        label="clothesline",
        phrase="a spare clothesline",
        sense=2,
        power=8,
        success="borrowed the spare clothesline and laced the hollyhock to the fence in three neat loops",
        fail="borrowed the spare clothesline and laced the stalk up fast, but the wind pulled harder than laundry ever could",
        qa_text="laced the hollyhock to the fence with a clothesline",
        tags={"rope", "support"},
    ),
    "thread": Support(
        id="thread",
        label="sewing thread",
        phrase="a spool of sewing thread",
        sense=1,
        power=3,
        success="wound sewing thread around the stalk, which would be a miracle if it worked",
        fail="wound sewing thread around the stalk, but thread for buttons is no match for a hollyhock reaching at the sky",
        qa_text="tried to tie the hollyhock with sewing thread",
        tags={"thread"},
    ),
}

GIRL_NAMES = ["Molly", "Tess", "Nell", "Dora", "Elsie", "Ada", "June", "Willa"]
BOY_NAMES = ["Eli", "Jem", "Toby", "Ned", "Cal", "Otis", "Finn", "Theo"]
HELPERS = [
    ("Grandma June", "grandmother"),
    ("Uncle Roy", "uncle"),
    ("Grandpa Seth", "grandfather"),
    ("Aunt May", "aunt"),
]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    booster: str
    watcher: str
    support: str
    hero: str
    gender: str
    helper_name: str
    helper_type: str
    delay: int = 0
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
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


KNOWLEDGE = {
    "hollyhock": [
        (
            "What is a hollyhock?",
            "A hollyhock is a tall garden flower with blossoms that open along a long stem. Some kinds can grow very high beside a fence or wall."
        )
    ],
    "support": [
        (
            "Why do tall plants sometimes need support?",
            "Very tall plants can lean when the wind pushes them. A stake or rope helps hold the stem upright so it does not bend or break."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. Looking from far away or too quickly can make mistakes more likely."
        )
    ],
    "wind": [
        (
            "Why can wind bend a plant?",
            "Wind pushes on leaves and stems over and over. If a stem is long and heavy, that pushing can make it lean or even snap."
        )
    ],
    "stake": [
        (
            "What does a garden stake do?",
            "A garden stake is a sturdy stick pushed into the ground beside a plant. You can tie the plant to it gently to help it stand up."
        )
    ],
    "rope": [
        (
            "Why can a rope help in a garden?",
            "A rope can hold something in place when it is tied carefully to something strong. Gardeners use soft ties so they do not hurt the plant."
        )
    ],
    "river": [
        (
            "Why is soil near a river often rich?",
            "Rivers carry tiny bits of mud and plant food called silt. When that settles on the bank, it can make the soil good for growing."
        )
    ],
}
KNOWLEDGE_ORDER = ["hollyhock", "support", "misunderstanding", "wind", "stake", "rope", "river"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    watcher_cfg = f["watcher_cfg"]
    place = f["place_cfg"]
    support = f["support_cfg"]
    outcome = f["outcome"]
    prompts = [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "hollyhock", lots of dialogue, and a misunderstanding in {place.label}.',
        f"Tell a playful story where {hero.id} and {helper.id} grow a hollyhock so tall that {watcher_cfg.label} mistakes it for {watcher_cfg.mistake}.",
        'Write a story with foreshadowing where someone warns that a giant flower will need tying before the wind gets strong.'
    ]
    if outcome == "saved":
        prompts.append(
            f"End with the hollyhock safely tied up with {support.label} and the town laughing at the mistake."
        )
    else:
        prompts.append(
            "End with the giant flower snapping, but dropping seeds that promise an even bigger garden next time."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    watcher = f["watcher"]
    watcher_cfg = f["watcher_cfg"]
    place = f["place_cfg"]
    booster = f["booster_cfg"]
    support = f["support_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {helper.id}, and {watcher.id}, who all got caught up in one enormous hollyhock. The story begins as simple planting and turns into a town-sized mix-up."
        ),
        (
            "Why did the hollyhock grow so tall?",
            f"It grew so tall because {hero.id} fed it {booster.label} in rich soil at {place.label}. In this tall-tale world, that was enough to make the flower shoot up higher than anyone expected."
        ),
        (
            "What was the warning before the trouble started?",
            f"{helper.id} noticed the wind and warned that a tall hollyhock would need to be tied before sunset. That warning foreshadowed the problem, because the stalk really did begin to lean once it grew huge."
        ),
    ]
    if f["misunderstood"]:
        qa.append(
            (
                f"What misunderstanding did {watcher.id} have?",
                f"{watcher.id} thought the leaning hollyhock was {watcher_cfg.mistake}. {watcher.pronoun().capitalize()} only saw the shape from far away, so the flower looked like something much bigger and stranger."
            )
        )
    if outcome == "saved":
        qa.append(
            (
                "How did they fix the problem?",
                f"They fixed it when {helper.id} {support.qa_text}. That kept the stem from leaning farther, and once the blossom opened everyone could plainly see it was only a hollyhock."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the flower standing high and safe while the town laughed at its mistake. The final bloom showed that fear had turned into pride."
            )
        )
    else:
        qa.append(
            (
                "Did they save the hollyhock?",
                f"No, the support came too late and the stalk snapped in the wind. But the flower dropped seeds, so the ending still promised new hollyhocks and a wiser plan next time."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with seeds spilling out after the giant stalk broke. That changed the mood from alarm and sadness into hope for a bigger garden later."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"hollyhock", "support", "misunderstanding", "wind"}
    support = f["support_cfg"]
    place = f["place_cfg"]
    if "stake" in support.tags:
        tags.add("stake")
    if "rope" in support.tags:
        tags.add("rope")
    if "river" in place.tags or "river" in f["booster_cfg"].tags:
        tags.add("river")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:14} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  strain={world.facts.get('strain')} outcome={world.facts.get('outcome')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="farmyard",
        booster="compost_tea",
        watcher="baker",
        support="stake",
        hero="Molly",
        gender="girl",
        helper_name="Grandma June",
        helper_type="grandmother",
        delay=0,
    ),
    StoryParams(
        place="riverside",
        booster="river_silt",
        watcher="ferryman",
        support="wagon_rope",
        hero="Eli",
        gender="boy",
        helper_name="Uncle Roy",
        helper_type="uncle",
        delay=1,
    ),
    StoryParams(
        place="millhill",
        booster="compost_tea",
        watcher="hill_shepherd",
        support="clothesline",
        hero="Tess",
        gender="girl",
        helper_name="Aunt May",
        helper_type="aunt",
        delay=2,
    ),
    StoryParams(
        place="riverside",
        booster="rain_barrel",
        watcher="baker",
        support="stake",
        hero="Ned",
        gender="boy",
        helper_name="Grandpa Seth",
        helper_type="grandfather",
        delay=0,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
giant_enough(P,B) :- soil(P,S), boost(B,G), S + G >= 5.
valid(P,B,W) :- place(P), booster(B), watcher(W),
                giant_enough(P,B), affords(P,B), watcher_ok(P,W).

sensible(Sup) :- support(Sup), sense(Sup,N), sense_min(M), N >= M.

% --- outcome model ---------------------------------------------------------
height(H) :- chosen_place(P), chosen_booster(B), soil(P,S), boost(B,G), H = S + G + 2.
strain(V) :- chosen_place(P), chosen_booster(B), delay(D), wind(P,W), height(H), V = W + H + D.
saved :- chosen_support(Sup), power(Sup,P), strain(V), P >= V.
outcome(saved) :- saved.
outcome(snapped) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("soil", place_id, place.soil))
        lines.append(asp.fact("wind", place_id, place.wind))
        for booster_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, booster_id))
        for watcher_id in sorted(place.watchers):
            lines.append(asp.fact("watcher_ok", place_id, watcher_id))
    for booster_id, booster in BOOSTERS.items():
        lines.append(asp.fact("booster", booster_id))
        lines.append(asp.fact("boost", booster_id, booster.boost))
    for watcher_id in WATCHERS:
        lines.append(asp.fact("watcher", watcher_id))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("sense", support_id, support.sense))
        lines.append(asp.fact("power", support_id, support.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_supports() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(s for (s,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_booster", params.booster),
            asp.fact("chosen_support", params.support),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "saved" if is_saved(
        PLACES[params.place],
        BOOSTERS[params.booster],
        SUPPORTS[params.support],
        params.delay,
    ) else "snapped"


def asp_verify() -> int:
    rc = 0

    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible_supports())
    p_sens = {s.id for s in sensible_supports()}
    if c_sens == p_sens:
        print(f"OK: sensible supports match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible supports: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
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
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a giant hollyhock, a windy warning, and a silly misunderstanding."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--booster", choices=BOOSTERS)
    ap.add_argument("--watcher", choices=WATCHERS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late they are before tying the stalk")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.support and SUPPORTS[args.support].sense < SENSE_MIN:
        raise StoryError(explain_support(args.support))

    if args.place and args.booster:
        place = PLACES[args.place]
        booster = BOOSTERS[args.booster]
        if args.booster not in place.affords or not giant_enough(place, booster):
            raise StoryError(explain_place_booster(place, booster))

    if args.place and args.watcher:
        place = PLACES[args.place]
        watcher = WATCHERS[args.watcher]
        if not watcher_plausible(place, watcher):
            raise StoryError(explain_watcher(place, watcher))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.booster is None or combo[1] == args.booster)
        and (args.watcher is None or combo[2] == args.watcher)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, booster_id, watcher_id = rng.choice(sorted(combos))
    support_id = args.support or rng.choice(sorted(s.id for s in sensible_supports()))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name, helper_type = rng.choice(HELPERS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        booster=booster_id,
        watcher=watcher_id,
        support=support_id,
        hero=hero,
        gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.booster not in BOOSTERS:
        raise StoryError(f"(Unknown booster: {params.booster})")
    if params.watcher not in WATCHERS:
        raise StoryError(f"(Unknown watcher: {params.watcher})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")
    if params.support in SUPPORTS and SUPPORTS[params.support].sense < SENSE_MIN:
        raise StoryError(explain_support(params.support))
    place = PLACES[params.place]
    booster = BOOSTERS[params.booster]
    watcher = WATCHERS[params.watcher]
    if params.booster not in place.affords or not giant_enough(place, booster):
        raise StoryError(explain_place_booster(place, booster))
    if not watcher_plausible(place, watcher):
        raise StoryError(explain_watcher(place, watcher))

    world = tell(
        place=place,
        booster=booster,
        watcher_cfg=watcher,
        support=SUPPORTS[params.support],
        hero_name=params.hero,
        hero_type=params.gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        delay=params.delay,
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
        print(f"sensible supports: {', '.join(asp_sensible_supports())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, booster, watcher) combos:\n")
        for place, booster, watcher in combos:
            print(f"  {place:10} {booster:12} {watcher}")
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
                f"### {p.hero}: {p.place}, {p.booster}, {p.watcher}, "
                f"{p.support}, {outcome_of(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
