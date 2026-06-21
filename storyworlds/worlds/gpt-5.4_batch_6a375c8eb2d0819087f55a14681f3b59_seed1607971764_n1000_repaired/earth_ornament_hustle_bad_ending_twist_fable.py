#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/earth_ornament_hustle_bad_ending_twist_fable.py
============================================================================

A standalone storyworld about woodland creatures shaping an ornament from earth,
hurrying it toward a winter tree, and discovering that the true gift was hidden
inside all along.

This world is built in a small fable-like domain:
- A maker shapes a soft earth ornament and tucks seeds inside it.
- A helper warns that soft earth should not be hung in a hustle.
- The maker chooses a drying method, then hangs the ornament on a branch.
- If the ornament is dry enough for that branch, it lasts through winter and
  breaks open in spring, scattering flowers.
- If it is not dry enough, it breaks at once, the seeds are lost, and the twist
  is revealed too late: the ornament was carrying spring.

The world includes both gentle and bad-ending variants, with the twist grounded
in the simulated seed state rather than pasted on as a final sentence.
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
    gender: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.gender == "female":
            table = {"subject": "she", "object": "her", "possessive": "her"}
            return table[case]
        if self.gender == "male":
            table = {"subject": "he", "object": "him", "possessive": "his"}
            return table[case]
        table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]
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
class Weather:
    id: str
    label: str
    sky: str
    air: str
    dry_bonus: int
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
class Method:
    id: str
    label: str
    sense: int
    dry_bonus: int
    line: str
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
class Branch:
    id: str
    label: str
    risk: int
    image: str
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
class Shape:
    id: str
    label: str
    phrase: str
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
class SeedKind:
    id: str
    label: str
    bloom: str
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
    weather: str
    method: str
    branch: str
    shape: str
    seeds: str
    maker: str
    maker_species: str
    maker_gender: str
    helper: str
    helper_species: str
    helper_gender: str
    trait: str
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


def _r_break(world: World) -> list[str]:
    ornament = world.get("ornament")
    branch = world.get("branch")
    seeds = world.get("seeds")
    if ornament.meters["hung"] < THRESHOLD:
        return []
    if ornament.meters["dryness"] >= branch.attrs["risk"]:
        return []
    sig = ("break", branch.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ornament.meters["broken"] += 1
    ornament.meters["fallen"] += 1
    seeds.meters["spilled"] += 1
    for eid in ("maker", "helper"):
        world.get(eid).memes["alarm"] += 1
    return ["__break__"]


def _r_loss(world: World) -> list[str]:
    seeds = world.get("seeds")
    if seeds.meters["spilled"] < THRESHOLD:
        return []
    sig = ("loss", seeds.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeds.meters["lost"] += 1
    world.get("maker").memes["regret"] += 1
    world.get("helper").memes["sadness"] += 1
    return ["__loss__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="break", tag="physical", apply=_r_break),
    Rule(name="loss", tag="physical", apply=_r_loss),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


WEATHERS = {
    "sunny": Weather(
        id="sunny",
        label="a clear noon",
        sky="the winter sun sat bright above the hedges",
        air="the air was crisp and kindly dry",
        dry_bonus=1,
        tags={"sun", "winter"},
    ),
    "breezy": Weather(
        id="breezy",
        label="a thin bright breeze",
        sky="pale light lay over the field",
        air="a patient breeze moved through the bare twigs",
        dry_bonus=0,
        tags={"wind", "winter"},
    ),
    "misty": Weather(
        id="misty",
        label="a silver mist",
        sky="the sky was hidden in a white blur",
        air="the air was wet enough to kiss every stone",
        dry_bonus=-1,
        tags={"mist", "winter"},
    ),
}

METHODS = {
    "hearth_shelf": Method(
        id="hearth_shelf",
        label="the hearth shelf",
        sense=3,
        dry_bonus=2,
        line="set the soft ornament on the warm shelf above the hearth and let it rest there",
        ending="It had time to grow firm beside the steady warmth.",
        tags={"hearth", "patience"},
    ),
    "window_ledge": Method(
        id="window_ledge",
        label="the window ledge",
        sense=3,
        dry_bonus=1,
        line="placed the ornament on the window ledge and let light and air visit it",
        ending="The earth slowly stiffened while the room stayed quiet.",
        tags={"window", "patience"},
    ),
    "rush_hang": Method(
        id="rush_hang",
        label="a hustle to the branch",
        sense=2,
        dry_bonus=0,
        line="gave the ornament only a few hasty breaths of air and hurried straight to the tree in a foolish hustle",
        ending="Soft earth still kept the maker's thumbprints.",
        tags={"hustle", "haste"},
    ),
    "oven_blast": Method(
        id="oven_blast",
        label="the hot oven mouth",
        sense=1,
        dry_bonus=3,
        line="held the ornament too close to a roaring oven mouth",
        ending="The heat was harsher than wisdom.",
        tags={"heat", "bad_idea"},
    ),
}

BRANCHES = {
    "low": Branch(
        id="low",
        label="a low branch",
        risk=1,
        image="where even a rabbit could study it from the roots",
        tags={"tree"},
    ),
    "high": Branch(
        id="high",
        label="a high branch",
        risk=2,
        image="where the winter wind poked and tugged at every little thing",
        tags={"tree", "wind"},
    ),
}

SHAPES = {
    "star": Shape(
        id="star",
        label="star",
        phrase="a little star-shaped ornament",
        tags={"ornament"},
    ),
    "moon": Shape(
        id="moon",
        label="moon",
        phrase="a curved moon ornament",
        tags={"ornament"},
    ),
    "acorn": Shape(
        id="acorn",
        label="acorn",
        phrase="an acorn-shaped ornament",
        tags={"ornament", "oak"},
    ),
}

SEED_KINDS = {
    "clover": SeedKind(
        id="clover",
        label="clover seeds",
        bloom="small green clover and white blossoms",
        tags={"seed", "clover"},
    ),
    "marigold": SeedKind(
        id="marigold",
        label="marigold seeds",
        bloom="round marigolds bright as little suns",
        tags={"seed", "flower"},
    ),
    "poppy": SeedKind(
        id="poppy",
        label="poppy seeds",
        bloom="red poppies that nodded in the spring wind",
        tags={"seed", "flower"},
    ),
}

MAKERS = [
    ("Pica", "magpie", "female"),
    ("Moss", "mole", "male"),
    ("Brindle", "fox", "female"),
    ("Ash", "squirrel", "male"),
]

HELPERS = [
    ("Tansy", "tortoise", "female"),
    ("Reed", "rabbit", "male"),
    ("Bramble", "badger", "female"),
    ("Thistle", "hedgehog", "male"),
]

TRAITS = ["careful", "slow", "thoughtful", "steady", "cautious"]


def practical_method(weather: Weather, method: Method) -> bool:
    if method.id == "window_ledge" and weather.id == "misty":
        return False
    return True


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def drying_score(weather: Weather, method: Method) -> int:
    return weather.dry_bonus + method.dry_bonus


def survives(weather: Weather, method: Method, branch: Branch) -> bool:
    return drying_score(weather, method) >= branch.risk


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for wid, weather in WEATHERS.items():
        for mid, method in METHODS.items():
            if method.sense < SENSE_MIN:
                continue
            if not practical_method(weather, method):
                continue
            for bid in BRANCHES:
                combos.append((wid, mid, bid))
    return combos


def predict_break(world: World, branch_id: str) -> bool:
    sim = world.copy()
    sim.get("ornament").meters["hung"] += 1
    sim.get("branch").attrs["risk"] = BRANCHES[branch_id].risk
    propagate(sim, narrate=False)
    return sim.get("ornament").meters["broken"] >= THRESHOLD


def introduce(world: World, maker: Entity, helper: Entity, weather: Weather) -> None:
    world.say(
        f"In the lean heart of winter, {weather.sky}, and {weather.air}. "
        f"{maker.id} the {maker.type} looked at the bare oak and wished to give it one brave ornament."
    )
    world.say(
        f"Nearby stood {helper.id} the {helper.type}, a {helper.attrs['trait']} friend "
        f"who believed that good things grow stronger when they are allowed their proper time."
    )


def shape_ornament(world: World, maker: Entity, shape: Shape, seeds: SeedKind) -> None:
    ornament = world.get("ornament")
    seed_ent = world.get("seeds")
    ornament.meters["soft"] = 1.0
    seed_ent.meters["hidden"] = 1.0
    maker.memes["pride"] += 1
    world.say(
        f"{maker.id} kneaded dark earth with a little water and shaped {shape.phrase}. "
        f"Before the clay closed, {maker.pronoun()} tucked in {seeds.label} and smiled."
    )
    world.say(
        f'"The oak shall wear this before dusk," said {maker.id}. '
        f'The small thing looked like only an ornament, but it carried more than winter could see.'
    )


def warning(world: World, maker: Entity, helper: Entity, branch: Branch) -> None:
    world.say(
        f'{helper.id} touched the soft earth with one careful paw. '
        f'"It is lovely," {helper.pronoun()} said, "but do not let a hustle choose its hour. '
        f'Soft earth is proud for a moment and broken after. '
        f'If you hang it on {branch.label}, {branch.image}, it must be firm first."'
    )
    maker.memes["impatience"] += 1
    helper.memes["care"] += 1
    world.facts["predicted_break"] = predict_break(world, branch.id)


def dry_step(world: World, maker: Entity, method: Method) -> None:
    ornament = world.get("ornament")
    score = world.facts["dry_score"]
    ornament.meters["dryness"] = float(score)
    if score >= 1:
        ornament.meters["soft"] = 0.0
    world.say(
        f"But {maker.id} chose {method.label}. {maker.pronoun().capitalize()} {method.line}. "
        f"{method.ending}"
    )


def hang_step(world: World, maker: Entity, branch: Branch) -> None:
    ornament = world.get("ornament")
    ornament.meters["hung"] += 1
    world.get("branch").attrs["risk"] = branch.risk
    world.say(
        f"Soon {maker.id} climbed to {branch.label}, {branch.image}, and tied the earth ornament there."
    )
    propagate(world, narrate=False)


def good_ending(world: World, maker: Entity, helper: Entity, seeds: SeedKind, branch: Branch) -> None:
    maker.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"The branch held still. The little ornament kept watch through frost, moonlight, and the long quiet weeks."
    )
    world.para()
    world.say(
        f"When spring rain finally came, the shell of earth softened in the kind way instead of the foolish one. "
        f"It opened and let {seeds.label} fall beneath the oak."
    )
    world.say(
        f"Then the twist of the winter gift was made plain: the ornament had not been made only to be seen. "
        f"It had been carrying {seeds.bloom} for the earth below."
    )
    world.say(
        f"So {maker.id} and {helper.id} learned that patience can make even a small decoration into tomorrow."
    )


def bad_ending(world: World, maker: Entity, helper: Entity, seeds: SeedKind, branch: Branch) -> None:
    ornament = world.get("ornament")
    seed_ent = world.get("seeds")
    ornament.meters["broken"] = max(ornament.meters["broken"], 1.0)
    seed_ent.meters["spilled"] = max(seed_ent.meters["spilled"], 1.0)
    seed_ent.meters["lost"] = max(seed_ent.meters["lost"], 1.0)
    maker.memes["regret"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"But the soft ornament had only borrowed the shape of strength. "
        f"The branch shook once, and the earth shell split. It fell, burst on the hard path, and the hidden seeds scattered."
    )
    world.say(
        f"Sparrows darted down and pecked the seeds away before the ground could keep them."
    )
    world.para()
    world.say(
        f"Only then did {maker.id} understand the twist of the gift. It had never been only an ornament for the tree. "
        f"It had been spring tucked inside a little coat of earth."
    )
    world.say(
        f"Because {maker.pronoun()} had let hustle rule the hour, neither branch nor soil kept the treasure. "
        f"The oak stood bare, and when warm days returned, no {seeds.bloom} rose there at all."
    )
    world.say(
        f"So the creatures of the hedgerow said afterward: haste may hang a gift quickly, but it can also empty it."
    )


def tell(
    weather: Weather,
    method: Method,
    branch: Branch,
    shape: Shape,
    seeds: SeedKind,
    maker_name: str,
    maker_species: str,
    maker_gender: str,
    helper_name: str,
    helper_species: str,
    helper_gender: str,
    trait: str,
) -> World:
    world = World()

    maker = world.add(
        Entity(
            id="maker",
            kind="character",
            type=maker_species,
            label=maker_name,
            gender=maker_gender,
            role="maker",
            attrs={"name": maker_name},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_species,
            label=helper_name,
            gender=helper_gender,
            role="helper",
            attrs={"name": helper_name, "trait": trait},
            traits=[trait],
        )
    )
    world.add(Entity(id="tree", type="oak", label="the oak"))
    world.add(Entity(id="branch", type="branch", label=branch.label, attrs={"risk": branch.risk}))
    world.add(Entity(id="ornament", type="ornament", label=shape.label))
    world.add(Entity(id="seeds", type="seeds", label=seeds.label))

    world.facts = {
        "weather": weather,
        "method": method,
        "branch_cfg": branch,
        "shape": shape,
        "seed_cfg": seeds,
        "maker_ent": maker,
        "helper_ent": helper,
        "maker_name": maker_name,
        "helper_name": helper_name,
        "dry_score": drying_score(weather, method),
        "predicted_break": False,
        "outcome": "",
    }

    introduce(world, maker, helper, weather)
    shape_ornament(world, maker, shape, seeds)

    world.para()
    warning(world, maker, helper, branch)
    dry_step(world, maker, method)
    hang_step(world, maker, branch)

    world.para()
    if world.get("ornament").meters["broken"] >= THRESHOLD:
        world.facts["outcome"] = "broken"
        bad_ending(world, maker, helper, seeds, branch)
    else:
        world.facts["outcome"] = "bloomed"
        good_ending(world, maker, helper, seeds, branch)

    return world


KNOWLEDGE = {
    "earth": [
        (
            "What is earth in a garden or field?",
            "Earth is the soil on the ground. Plants grow in it, and when it is wet enough it can be shaped like clay."
        )
    ],
    "ornament": [
        (
            "What is an ornament?",
            "An ornament is a thing made to decorate something else. People or animals may hang one on a branch, a wall, or a tree to make it look special."
        )
    ],
    "seed": [
        (
            "What is hidden inside a seed?",
            "A seed holds the beginning of a new plant. If it reaches good soil, water, and time, it can grow into leaves and flowers."
        )
    ],
    "hearth": [
        (
            "What is a hearth?",
            "A hearth is the warm place around a fireplace. It can gently warm things nearby when the fire is safe and steady."
        )
    ],
    "window": [
        (
            "Why can a window ledge help something dry?",
            "A window ledge can get light and moving air. Those help water leave a soft thing slowly, so it becomes firmer."
        )
    ],
    "hustle": [
        (
            "What does hustle mean in a story like this?",
            "Hustle means rushing and hurrying instead of taking proper time. Sometimes it helps you move fast, but it can also make you careless."
        )
    ],
    "winter": [
        (
            "Why do trees look bare in winter?",
            "Many trees rest in winter and lose their leaves. Their branches look bare, but they are still alive and waiting for spring."
        )
    ],
}
KNOWLEDGE_ORDER = ["earth", "ornament", "seed", "hearth", "window", "hustle", "winter"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maker = f["maker_ent"]
    helper = f["helper_ent"]
    method = f["method"]
    branch = f["branch_cfg"]
    shape = f["shape"]
    seeds = f["seed_cfg"]
    bad = f["outcome"] == "broken"
    if bad:
        return [
            'Write a short fable for a young child that uses the words "earth", "ornament", and "hustle".',
            f"Tell a woodland fable where {maker.attrs['name']} the {maker.type} shapes a soft earth ornament with {seeds.label} inside, ignores {helper.attrs['name']} the {helper.type}, and hangs it on {branch.label} too soon.",
            "Write a bad-ending fable with a twist: the decoration that breaks was secretly carrying next spring.",
        ]
    return [
        'Write a short fable for a young child that uses the words "earth", "ornament", and "hustle".',
        f"Tell a woodland fable where {maker.attrs['name']} the {maker.type} makes {shape.phrase}, almost lets hustle rule the hour, but ends with a hidden gift for the earth.",
        "Write a fable with a twist in which an ornament turns out to be more than a decoration.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker = f["maker_ent"]
    helper = f["helper_ent"]
    weather = f["weather"]
    method = f["method"]
    branch = f["branch_cfg"]
    shape = f["shape"]
    seeds = f["seed_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {maker.attrs['name']} the {maker.type} and {helper.attrs['name']} the {helper.type}. One wanted to make a gift quickly, and the other tried to slow the choice with wisdom."
        ),
        (
            "What did the maker create?",
            f"{maker.attrs['name']} shaped {shape.phrase} from earth and hid {seeds.label} inside it. It looked like a decoration, but it was carrying something living too."
        ),
        (
            f"Why did {helper.attrs['name']} warn against a hustle?",
            f"{helper.attrs['name']} could see that the earth ornament was still soft. {helper.pronoun().capitalize()} warned that a hurried gift might break before it could do its true work."
        ),
        (
            f"How did {maker.attrs['name']} try to prepare the ornament?",
            f"{maker.attrs['name']} chose {method.label} on {weather.label}. That mattered because the weather and the method together decided whether the soft earth became firm enough."
        ),
    ]

    if outcome == "broken":
        qa.append(
            (
                "What happened when the ornament was hung?",
                f"It broke and fell from {branch.label}, and the hidden seeds spilled onto the path. The bad ending came because the ornament was softer than the branch's shaking could bear."
            )
        )
        qa.append(
            (
                "What was the twist at the end?",
                f"The twist was that the ornament had not been only for show. It had been carrying {seeds.label} so spring flowers could grow for the earth below."
            )
        )
        qa.append(
            (
                "Why was the ending sad?",
                f"The seeds were pecked away before they could reach the soil, so the oak got no flowers in spring. A quick choice spoiled both the decoration and the future hidden inside it."
            )
        )
    else:
        qa.append(
            (
                "What happened when spring came?",
                f"When spring rain softened the shell at the right time, it opened and dropped the seeds under the oak. Then {seeds.bloom} began to grow there."
            )
        )
        qa.append(
            (
                "What was the twist at the end?",
                f"The twist was that the ornament had secretly been a little seed carrier. It decorated the branch for a season, then fed the earth with a new beginning."
            )
        )
        qa.append(
            (
                "What lesson did the maker learn?",
                f"{maker.attrs['name']} learned that patience can protect a gift better than a foolish hustle can. Waiting helped the ornament keep both its beauty and its hidden purpose."
            )
        )

    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"earth", "ornament", "seed", "winter"}
    method = world.facts["method"]
    if "hearth" in method.tags:
        tags.add("hearth")
    if "window" in method.tags:
        tags.add("window")
    if "hustle" in method.tags:
        tags.add("hustle")
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
        lines.append(f"  {ent.id:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    return (
        f"(No story: '{method_id}' is known to the world, but it is refused because its common-sense score "
        f"is {method.sense}, below the minimum of {SENSE_MIN}. Try one of: "
        f"{', '.join(sorted(m.id for m in sensible_methods()))}.)"
    )


def explain_weather_method(weather: Weather, method: Method) -> str:
    if method.id == "window_ledge" and weather.id == "misty":
        return (
            "(No story: a misty day leaves the window ledge damp, so it is not a believable way "
            "to dry a soft earth ornament.)"
        )
    return "(No story: that weather and drying method do not make sense together.)"


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

blocked(window_ledge, misty).

practical(W, M) :- weather(W), method(M), not blocked(M, W).
valid(W, M, B) :- weather(W), method(M), branch(B), sensible(M), practical(W, M).

dryness(DW + DM) :- chosen_weather(W), chosen_method(M),
                    weather_bonus(W, DW), method_bonus(M, DM).

outcome(bloomed) :- chosen_branch(B), risk(B, R), dryness(D), D >= R.
outcome(broken)  :- chosen_branch(B), risk(B, R), dryness(D), D < R.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("weather_bonus", wid, weather.dry_bonus))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("method_bonus", mid, method.dry_bonus))
    for bid, branch in BRANCHES.items():
        lines.append(asp.fact("branch", bid))
        lines.append(asp.fact("risk", bid, branch.risk))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_branch", params.branch),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    weather = WEATHERS[params.weather]
    method = METHODS[params.method]
    branch = BRANCHES[params.branch]
    return "bloomed" if survives(weather, method, branch) else "broken"


CURATED = [
    StoryParams(
        weather="misty",
        method="rush_hang",
        branch="high",
        shape="star",
        seeds="poppy",
        maker="Pica",
        maker_species="magpie",
        maker_gender="female",
        helper="Tansy",
        helper_species="tortoise",
        helper_gender="female",
        trait="steady",
    ),
    StoryParams(
        weather="sunny",
        method="hearth_shelf",
        branch="high",
        shape="moon",
        seeds="marigold",
        maker="Moss",
        maker_species="mole",
        maker_gender="male",
        helper="Reed",
        helper_species="rabbit",
        helper_gender="male",
        trait="careful",
    ),
    StoryParams(
        weather="breezy",
        method="window_ledge",
        branch="low",
        shape="acorn",
        seeds="clover",
        maker="Brindle",
        maker_species="fox",
        maker_gender="female",
        helper="Bramble",
        helper_species="badger",
        helper_gender="female",
        trait="thoughtful",
    ),
    StoryParams(
        weather="sunny",
        method="rush_hang",
        branch="high",
        shape="star",
        seeds="clover",
        maker="Ash",
        maker_species="squirrel",
        maker_gender="male",
        helper="Thistle",
        helper_species="hedgehog",
        helper_gender="male",
        trait="slow",
    ),
    StoryParams(
        weather="sunny",
        method="window_ledge",
        branch="high",
        shape="moon",
        seeds="poppy",
        maker="Pica",
        maker_species="magpie",
        maker_gender="female",
        helper="Bramble",
        helper_species="badger",
        helper_gender="female",
        trait="cautious",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: an earth ornament, a winter hustle, and a fable-like twist."
    )
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--branch", choices=BRANCHES)
    ap.add_argument("--shape", choices=SHAPES)
    ap.add_argument("--seeds", choices=SEED_KINDS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible weather/method/branch combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test ordinary generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))
    if args.weather and args.method:
        weather = WEATHERS[args.weather]
        method = METHODS[args.method]
        if method.sense >= SENSE_MIN and not practical_method(weather, method):
            raise StoryError(explain_weather_method(weather, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.weather is None or combo[0] == args.weather)
        and (args.method is None or combo[1] == args.method)
        and (args.branch is None or combo[2] == args.branch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    weather_id, method_id, branch_id = rng.choice(sorted(combos))
    shape_id = args.shape or rng.choice(sorted(SHAPES))
    seed_id = args.seeds or rng.choice(sorted(SEED_KINDS))

    maker_name, maker_species, maker_gender = rng.choice(MAKERS)
    helper_choices = [h for h in HELPERS if h[0] != maker_name]
    helper_name, helper_species, helper_gender = rng.choice(helper_choices)
    trait = rng.choice(TRAITS)

    return StoryParams(
        weather=weather_id,
        method=method_id,
        branch=branch_id,
        shape=shape_id,
        seeds=seed_id,
        maker=maker_name,
        maker_species=maker_species,
        maker_gender=maker_gender,
        helper=helper_name,
        helper_species=helper_species,
        helper_gender=helper_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("weather", WEATHERS),
        ("method", METHODS),
        ("branch", BRANCHES),
        ("shape", SHAPES),
        ("seeds", SEED_KINDS),
    ):
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(No story: unknown {field_name} '{value}'.)")
    if params.method not in METHODS or METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))
    if not practical_method(WEATHERS[params.weather], METHODS[params.method]):
        raise StoryError(explain_weather_method(WEATHERS[params.weather], METHODS[params.method]))

    world = tell(
        weather=WEATHERS[params.weather],
        method=METHODS[params.method],
        branch=BRANCHES[params.branch],
        shape=SHAPES[params.shape],
        seeds=SEED_KINDS[params.seeds],
        maker_name=params.maker,
        maker_species=params.maker_species,
        maker_gender=params.maker_gender,
        helper_name=params.helper,
        helper_species=params.helper_species,
        helper_gender=params.helper_gender,
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
    python_sensible = {m.id for m in sensible_methods()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible methods match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        emit(smoke, trace=False, qa=False, header="")
        print("\nOK: smoke generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
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
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (weather, method, branch) combos:\n")
        for weather, method, branch in combos:
            print(f"  {weather:7} {method:12} {branch}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = (
                f"### {p.maker} the {p.maker_species}: {p.method} on {p.branch} "
                f"({p.weather}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
