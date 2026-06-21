#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/peel_bad_ending_bravery_dialogue_folk_tale.py
=======================================================================

A standalone story world in a small folk-tale domain: a brave village child must
bring home healing fruit peel from the far grove while the river runs dark and
cold. The world models whether the child crosses sensibly, whether help is
accepted, and whether brave words turn into wise courage or reckless boasting.

This file follows the Storyweavers single-world contract:
- one standalone stdlib script
- eager shared results import
- lazy ASP import in helper functions
- classical simulation with typed entities, meters, and memes
- Python reasonableness gate plus inline ASP twin
- story, prompts, story-grounded QA, and world-knowledge QA from world state

Run it
------
    python storyworlds/worlds/gpt-5.4/peel_bad_ending_bravery_dialogue_folk_tale.py
    python storyworlds/worlds/gpt-5.4/peel_bad_ending_bravery_dialogue_folk_tale.py --weather rain --crossing stepping_stones
    python storyworlds/worlds/gpt-5.4/peel_bad_ending_bravery_dialogue_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/peel_bad_ending_bravery_dialogue_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/peel_bad_ending_bravery_dialogue_folk_tale.py --verify
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
        female = {"girl", "mother", "woman", "grandmother", "daughter"}
        male = {"boy", "father", "man", "grandfather", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
        }.get(self.type, self.label or self.type)
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
    sky: str
    river_line: str
    severity: int
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
class Fruit:
    id: str
    label: str
    tree: str
    peel_phrase: str
    scent: str
    weight: int
    tea_name: str
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
class Crossing:
    id: str
    label: str
    phrase: str
    keeper: str
    max_water: int
    stability: int
    risk: int
    success_text: str
    fail_text: str
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
class Companion:
    id: str
    label: str
    phrase: str
    speech: str
    aid: int
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
class Manner:
    id: str
    boast: str
    care: int
    listens: bool
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
    fruit: str
    crossing: str
    companion: str
    manner: str
    child_name: str
    child_gender: str
    elder_type: str
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


def _r_slip_soak(world: World) -> list[str]:
    child = world.get("child")
    peel = world.get("peel")
    river = world.get("river")
    out: list[str] = []
    if child.meters["stumble"] < THRESHOLD:
        return out
    sig = ("slip_soak",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    river.meters["splashed"] += 1
    peel.meters["wet"] += 1
    out.append("__slip__")
    return out


def _r_wet_ruins_peel(world: World) -> list[str]:
    peel = world.get("peel")
    elder = world.get("elder")
    child = world.get("child")
    out: list[str] = []
    if peel.meters["wet"] < THRESHOLD:
        return out
    sig = ("ruin",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    peel.meters["ruined"] += 1
    elder.memes["hope"] = 0.0
    elder.memes["sorrow"] += 1
    child.memes["grief"] += 1
    out.append("__ruined__")
    return out


def _r_dry_peel_heals(world: World) -> list[str]:
    peel = world.get("peel")
    elder = world.get("elder")
    child = world.get("child")
    out: list[str] = []
    if peel.attrs.get("home") != "hut":
        return out
    if peel.meters["ruined"] >= THRESHOLD:
        return out
    sig = ("healed",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    elder.meters["healed"] += 1
    elder.meters["sick"] = 0.0
    elder.memes["hope"] += 1
    child.memes["relief"] += 1
    out.append("__healed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip_soak", tag="physical", apply=_r_slip_soak),
    Rule(name="wet_ruins_peel", tag="physical", apply=_r_wet_ruins_peel),
    Rule(name="dry_peel_heals", tag="physical", apply=_r_dry_peel_heals),
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


WEATHERS = {
    "mist": Weather(
        id="mist",
        sky="a pale mist",
        river_line="The Black Stream whispered under a veil of mist.",
        severity=1,
        tags={"river", "weather"},
    ),
    "wind": Weather(
        id="wind",
        sky="a hard wind",
        river_line="The Black Stream slapped its banks while the wind worried the reeds.",
        severity=2,
        tags={"river", "weather", "wind"},
    ),
    "rain": Weather(
        id="rain",
        sky="cold rain",
        river_line="The Black Stream ran high and brown after the rain.",
        severity=3,
        tags={"river", "weather", "rain"},
    ),
}

FRUITS = {
    "orange": Fruit(
        id="orange",
        label="orange",
        tree="orange tree",
        peel_phrase="a curl of bright orange peel",
        scent="smelled sweet and warm",
        weight=1,
        tea_name="orange-peel tea",
        tags={"orange", "peel", "tea"},
    ),
    "lemon": Fruit(
        id="lemon",
        label="lemon",
        tree="lemon tree",
        peel_phrase="a ribbon of yellow peel",
        scent="smelled sharp and clean",
        weight=1,
        tea_name="lemon-peel tea",
        tags={"lemon", "peel", "tea"},
    ),
    "pomelo": Fruit(
        id="pomelo",
        label="pomelo",
        tree="pomelo tree",
        peel_phrase="a thick curl of pale peel",
        scent="smelled rich and bitter-sweet",
        weight=2,
        tea_name="pomelo-peel tea",
        tags={"pomelo", "peel", "tea"},
    ),
}

CROSSINGS = {
    "stepping_stones": Crossing(
        id="stepping_stones",
        label="stepping stones",
        phrase="the old stepping stones",
        keeper="the stones",
        max_water=1,
        stability=1,
        risk=1,
        success_text="placed each foot with care and reached the far bank with only silver drops on the shoes",
        fail_text="trusted the water too much, and one stone rolled under a hurried foot",
        tags={"stones", "river"},
    ),
    "rope_bridge": Crossing(
        id="rope_bridge",
        label="rope bridge",
        phrase="the swaying rope bridge",
        keeper="the bridge",
        max_water=2,
        stability=1,
        risk=2,
        success_text="held the ropes, let the bridge finish its swinging, and crossed above the water",
        fail_text="ran onto the bridge while it was still swaying, and the planks kicked under small feet",
        tags={"bridge", "river"},
    ),
    "ferry": Crossing(
        id="ferry",
        label="ferry",
        phrase="the ferryman's little ferry",
        keeper="the ferryman",
        max_water=3,
        stability=3,
        risk=0,
        success_text="waited, asked, and sat still while the ferry nosed through the dark water",
        fail_text="tried to leap in before the boat settled, and the peel bundle slipped into the spray",
        tags={"ferry", "river", "boat"},
    ),
}

COMPANIONS = {
    "sparrow": Companion(
        id="sparrow",
        label="sparrow",
        phrase="a brown sparrow from the thatch",
        speech='"Go softly, little one. Even brave feet should listen."',
        aid=0,
        tags={"sparrow", "bird"},
    ),
    "dog": Companion(
        id="dog",
        label="dog",
        phrase="the baker's old dog",
        speech='"I cannot speak as people do," the dog seemed to say with his steady eyes, "but I know the safe pace of roads."',
        aid=1,
        tags={"dog", "animal"},
    ),
    "tortoise": Companion(
        id="tortoise",
        label="tortoise",
        phrase="a pond tortoise with a mossy shell",
        speech='"Slow shells outlive quick boasts," said the tortoise. "Take the road that keeps what you carry."',
        aid=2,
        tags={"tortoise", "animal"},
    ),
}

MANNERS = {
    "humble": Manner(
        id="humble",
        boast='"I am afraid," said the child, "but I will go carefully, and I will listen."',
        care=1,
        listens=True,
        tags={"bravery", "listening"},
    ),
    "boastful": Manner(
        id="boastful",
        boast='"The stream may roar if it likes," said the child. "My brave feet need no counsel."',
        care=0,
        listens=False,
        tags={"bravery", "boast"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Lina", "Tala", "Niva", "Suri"]
BOY_NAMES = ["Ivo", "Toma", "Milo", "Rafi", "Naren", "Pavel"]


def crossing_allowed(weather: Weather, crossing: Crossing) -> bool:
    return weather.severity <= crossing.max_water


def outcome_scores(params: StoryParams) -> tuple[int, int]:
    weather = WEATHERS[params.weather]
    fruit = FRUITS[params.fruit]
    crossing = CROSSINGS[params.crossing]
    companion = COMPANIONS[params.companion]
    manner = MANNERS[params.manner]
    support = crossing.stability + companion.aid + manner.care
    danger = weather.severity + crossing.risk + fruit.weight
    return support, danger


def outcome_of(params: StoryParams) -> str:
    support, danger = outcome_scores(params)
    return "safe" if support >= danger else "bad_end"


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for wid, weather in WEATHERS.items():
        for fid in FRUITS:
            for cid, crossing in CROSSINGS.items():
                if crossing_allowed(weather, crossing):
                    out.append((wid, fid, cid))
    return out


def predict_crossing(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    child = sim.get("child")
    peel = sim.get("peel")
    support, danger = outcome_scores(params)
    if support < danger:
        child.meters["stumble"] += 1
        propagate(sim, narrate=False)
        peel.attrs["home"] = "riverbank"
    else:
        peel.attrs["home"] = "hut"
        propagate(sim, narrate=False)
    return {
        "ruined": peel.meters["ruined"] >= THRESHOLD,
        "healed": sim.get("elder").meters["healed"] >= THRESHOLD,
        "fear": child.memes["fear"],
    }


def opening(world: World, child: Entity, elder: Entity, weather: Weather, fruit: Fruit) -> None:
    child.memes["love"] += 1
    elder.meters["sick"] += 1
    elder.memes["hope"] += 1
    world.say(
        f"In the days when rivers were said to remember every footstep, {child.id} lived with "
        f"{child.pronoun('possessive')} {elder.label_word} in a clay hut beside the Black Stream."
    )
    world.say(
        f"That morning {weather.sky} lay over the village, and {weather.river_line} "
        f"{elder.label_word.capitalize()} shivered beneath her quilt and whispered that only "
        f"{fruit.tea_name} could warm her old chest."
    )


def request(world: World, child: Entity, elder: Entity, fruit: Fruit) -> None:
    world.say(
        f'"Beyond the stream stands the {fruit.tree}," said {elder.label_word}. '
        f'"Bring me {fruit.peel_phrase}, and I will boil it with honey."'
    )


def vow(world: World, child: Entity, elder: Entity, manner: Manner) -> None:
    child.memes["bravery"] += 1
    child.memes["fear"] += 1
    world.say(
        f"{child.id} looked at the dark doorway and then at {elder.label_word}'s shaking hands. "
        f'{manner.boast}'
    )


def companion_arrives(world: World, child: Entity, companion: Companion) -> None:
    helper = world.get("companion")
    helper.memes["care"] += 1
    world.say(
        f"At the threshold waited {companion.phrase}. {companion.speech}"
    )
    if companion.aid >= 1:
        child.memes["trust"] += 1


def set_out(world: World, child: Entity, weather: Weather, crossing: Crossing, fruit: Fruit) -> None:
    river = world.get("river")
    peel = world.get("peel")
    river.meters["danger"] = float(weather.severity)
    peel.attrs["home"] = "grove"
    world.say(
        f"So {child.id} took a small knife and a cloth for the peel and set out toward "
        f"{crossing.phrase}. The child was brave enough to go, though the stream made even the reeds bow."
    )


def warning(world: World, child: Entity, elder: Entity, crossing: Crossing, params: StoryParams) -> None:
    pred = predict_crossing(world, params)
    world.facts["predicted_ruin"] = pred["ruined"]
    world.facts["predicted_heal"] = pred["healed"]
    if crossing.id == "ferry":
        extra = ' "Ask before you step in," called the ferryman from the near bank.'
    elif crossing.id == "rope_bridge":
        extra = ' "Hold and wait," creaked the bridge as if old wood had found a voice.'
    else:
        extra = ' "Watch the round stones," murmured the stream between them.'
    world.say(
        f"{elder.label_word.capitalize()} called after the child from the doorway, "
        f'"Keep the peel dry and come back with the sun still in the sky."{extra}'
    )


def grove_scene(world: World, child: Entity, fruit: Fruit) -> None:
    peel = world.get("peel")
    peel.attrs["home"] = "child"
    child.memes["hope"] += 1
    peel.meters["fresh"] += 1
    world.say(
        f"In the far grove, {child.id} cut {fruit.peel_phrase} from the fruit. It "
        f"{fruit.scent}, and the child wrapped it in the cloth as if wrapping a small promise."
    )


def cross_back(world: World, child: Entity, crossing: Crossing, companion: Companion, params: StoryParams) -> None:
    peel = world.get("peel")
    support, danger = outcome_scores(params)
    world.facts["support"] = support
    world.facts["danger"] = danger
    world.say(
        f"By dusk {child.id} stood again at {crossing.phrase}, with the peel tucked close and "
        f"{companion.label} beside {child.pronoun('object')}."
    )
    if support >= danger:
        peel.attrs["home"] = "hut"
        world.say(
            f'{child.id} remembered every warning. "{crossing.keeper.capitalize()}, let me pass without folly," '
            f"the child said, and then {crossing.success_text}."
        )
        propagate(world, narrate=False)
    else:
        child.meters["stumble"] += 1
        world.say(
            f'{child.id} lifted {child.pronoun("possessive")} chin and said, "A bold heart is enough." '
            f"But {crossing.fail_text}."
        )
        propagate(world, narrate=False)
        peel.attrs["home"] = "riverbank"


def good_ending(world: World, child: Entity, elder: Entity, fruit: Fruit, companion: Companion) -> None:
    child.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"When {child.id} reached the hut, {elder.label_word} set the kettle on the coals and brewed the "
        f"{fruit.tea_name}. Steam rose sweetly, and color came back into her cheeks."
    )
    world.say(
        f'"Bravery is best when it walks with listening," said {elder.label_word}. '
        f'{child.id} nodded, and even the {companion.label} seemed pleased. '
        f"That night the hut glowed warm against the dark."
    )


def bad_ending(world: World, child: Entity, elder: Entity, fruit: Fruit, crossing: Crossing) -> None:
    child.memes["remorse"] += 1
    elder.memes["sorrow"] += 1
    peel = world.get("peel")
    where = "the black water" if peel.meters["wet"] >= THRESHOLD else "the dark bank"
    world.say(
        f"The peel was spoiled by {where}, and no {fruit.tea_name} was brewed that night. "
        f"{child.id} came home empty-handed, with river water on the hem and silence in the mouth."
    )
    world.say(
        f'{elder.label_word.capitalize()} drew the child close and said only, "A brave heart must still heed a warning." '
        f"But the hut stayed cold, the kettle stayed empty, and the wind told the tale through the cracks until dawn."
    )


def tell(
    weather: Weather,
    fruit: Fruit,
    crossing: Crossing,
    companion_cfg: Companion,
    manner: Manner,
    child_name: str = "Anya",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"name": child_name},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_type,
        role="elder",
    ))
    helper_type = "animal"
    helper = world.add(Entity(
        id="companion",
        kind="character",
        type=helper_type,
        label=companion_cfg.label,
        role="companion",
        attrs={"speech": companion_cfg.speech},
    ))
    river = world.add(Entity(
        id="river",
        kind="thing",
        type="river",
        label="Black Stream",
        role="river",
    ))
    peel = world.add(Entity(
        id="peel",
        kind="thing",
        type="peel",
        label=fruit.peel_phrase,
        role="peel",
        attrs={"home": "tree"},
    ))

    world.facts.update(
        child=child,
        elder=elder,
        companion=helper,
        weather=weather,
        fruit=fruit,
        crossing=crossing,
        companion_cfg=companion_cfg,
        manner=manner,
        child_name=child_name,
    )

    opening(world, child, elder, weather, fruit)
    request(world, child, elder, fruit)
    world.para()
    vow(world, child, elder, manner)
    companion_arrives(world, child, companion_cfg)
    set_out(world, child, weather, crossing, fruit)
    warning(
        world,
        child,
        elder,
        crossing,
        StoryParams(
            weather=weather.id,
            fruit=fruit.id,
            crossing=crossing.id,
            companion=companion_cfg.id,
            manner=manner.id,
            child_name=child_name,
            child_gender=child_gender,
            elder_type=elder_type,
        ),
    )
    world.para()
    grove_scene(world, child, fruit)
    cross_back(
        world,
        child,
        crossing,
        companion_cfg,
        StoryParams(
            weather=weather.id,
            fruit=fruit.id,
            crossing=crossing.id,
            companion=companion_cfg.id,
            manner=manner.id,
            child_name=child_name,
            child_gender=child_gender,
            elder_type=elder_type,
        ),
    )
    world.para()
    if world.get("elder").meters["healed"] >= THRESHOLD:
        good_ending(world, child, elder, fruit, companion_cfg)
        outcome = "safe"
    else:
        bad_ending(world, child, elder, fruit, crossing)
        outcome = "bad_end"

    world.facts.update(
        outcome=outcome,
        peel_ruined=world.get("peel").meters["ruined"] >= THRESHOLD,
        elder_healed=world.get("elder").meters["healed"] >= THRESHOLD,
    )
    return world


def explain_rejection(weather: Weather, crossing: Crossing) -> str:
    return (
        f"(No story: {crossing.label} is not a believable crossing when the stream is under "
        f"{weather.sky}. Pick a crossing that can handle water severity {weather.severity}, "
        f"such as "
        f"{', '.join(cid for cid, c in CROSSINGS.items() if c.max_water >= weather.severity)}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    fruit = f["fruit"]
    crossing = f["crossing"]
    outcome = f["outcome"]
    name = f["child_name"]
    if outcome == "bad_end":
        end_line = "end sadly, with the lesson arriving too late."
    else:
        end_line = "end with the elder warmed and the child wiser."
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the word "peel" and a brave child crossing a river.',
        f"Tell a folk-tale story where {name} tries to bring home {fruit.peel_phrase} by way of {crossing.phrase}, with spoken warnings and spoken promises, and {end_line}",
        f"Write a dialogue-rich village tale about a sick {elder.label_word}, a dangerous crossing, and the difference between bravery and foolishness.",
    ]


KNOWLEDGE = {
    "peel": [
        (
            "What is peel on a fruit?",
            "Peel is the outside skin of a fruit. Some peels smell strong and can be used in cooking or tea.",
        )
    ],
    "orange": [
        (
            "What does orange peel smell like?",
            "Orange peel usually smells sweet and bright because it has tiny drops of fragrant oil in it.",
        )
    ],
    "lemon": [
        (
            "Why does lemon peel smell sharp?",
            "Lemon peel has strong citrus oil in it. That oil gives it a clean, sharp smell.",
        )
    ],
    "pomelo": [
        (
            "What is a pomelo?",
            "A pomelo is a very large citrus fruit, like a giant cousin of an orange or grapefruit.",
        )
    ],
    "tea": [
        (
            "How can fruit peel be used in tea?",
            "A grown-up can boil clean fruit peel in water to give the drink a warm smell and taste.",
        )
    ],
    "river": [
        (
            "Why can a river be dangerous after rain?",
            "Rain can make a river deeper, faster, and stronger. That means stones and banks can become slippery.",
        )
    ],
    "bridge": [
        (
            "Why should you hold still on a rope bridge?",
            "A rope bridge can sway when you rush. Holding on and moving slowly helps you keep your balance.",
        )
    ],
    "ferry": [
        (
            "What is a ferry?",
            "A ferry is a small boat that carries people across water. You should wait for it to settle before stepping in.",
        )
    ],
    "bravery": [
        (
            "What is true bravery?",
            "True bravery means doing a hard thing carefully. It is different from ignoring good advice.",
        )
    ],
    "animal": [
        (
            "Why do folk tales often give advice through animals?",
            "Animals in folk tales often speak for patience, caution, or kindness. Their words help show the lesson of the story.",
        )
    ],
}
KNOWLEDGE_ORDER = ["peel", "orange", "lemon", "pomelo", "tea", "river", "bridge", "ferry", "bravery", "animal"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    fruit = f["fruit"]
    crossing = f["crossing"]
    companion = f["companion_cfg"]
    manner = f["manner"]
    name = f["child_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a brave child, and {name}'s {elder.label_word} by the Black Stream. The story also follows the {companion.label} who goes along and gives a little help.",
        ),
        (
            f"Why did {name} go into the grove?",
            f"{name} went to fetch {fruit.peel_phrase} so {elder.label_word} could brew {fruit.tea_name}. The peel mattered because the elder was sick and hoped it would warm her.",
        ),
        (
            f"What did {name} say before leaving?",
            f"{name} spoke bravely before setting out. The words showed whether that bravery was careful and listening or proud and hurried.",
        ),
        (
            f"Why was {crossing.phrase} important?",
            f"It was the hard part of the journey home. The peel had to cross the stream dry, so the crossing decided whether the promise could be kept.",
        ),
    ]
    if f["outcome"] == "safe":
        qa.append(
            (
                f"How did {name} succeed?",
                f"{name} listened to the warnings, crossed with care, and kept the peel dry. Because the peel reached the hut safely, {elder.label_word} could brew the tea and recover.",
            )
        )
        qa.append(
            (
                f"What lesson did {elder.label_word} teach at the end?",
                f"{elder.label_word.capitalize()} said that bravery is best when it walks with listening. That means courage helped only because it was joined to patience and good sense.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the story end badly?",
                f"The crossing went wrong, the peel was spoiled, and no tea could be brewed that night. {name} was brave enough to go, but bravery without listening was not enough to save what {child.pronoun('subject')} carried.",
            )
        )
        qa.append(
            (
                f"How did {name} feel at the end?",
                f"{name} felt sorrow and remorse when returning empty-handed. The cold hut and empty kettle showed that the loss reached beyond one mistake.",
            )
        )
    if companion.aid >= 1:
        qa.append(
            (
                f"How did the {companion.label} help?",
                f"The {companion.label} did not carry the peel, but it steadied the child's choices. Its company mattered because the journey was fearful and the crossing demanded patience.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"peel", "tea", "river", "bravery"}
    tags |= set(f["fruit"].tags)
    tags |= set(f["crossing"].tags)
    tags |= set(f["companion_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        weather="mist",
        fruit="orange",
        crossing="stepping_stones",
        companion="tortoise",
        manner="humble",
        child_name="Anya",
        child_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        weather="wind",
        fruit="lemon",
        crossing="ferry",
        companion="dog",
        manner="humble",
        child_name="Milo",
        child_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        weather="wind",
        fruit="pomelo",
        crossing="rope_bridge",
        companion="sparrow",
        manner="boastful",
        child_name="Tala",
        child_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        weather="rain",
        fruit="orange",
        crossing="ferry",
        companion="dog",
        manner="boastful",
        child_name="Rafi",
        child_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        weather="mist",
        fruit="pomelo",
        crossing="rope_bridge",
        companion="tortoise",
        manner="humble",
        child_name="Lina",
        child_gender="girl",
        elder_type="grandmother",
    ),
]


ASP_RULES = r"""
valid(W,F,C) :- weather(W), fruit(F), crossing(C), severity(W,S), max_water(C,M), S <= M.

support(P) :- chosen_crossing(C), stability(C,St), chosen_companion(H), aid(H,A),
              chosen_manner(M), care(M,Ca), P = St + A + Ca.
danger(D)  :- chosen_weather(W), severity(W,S), chosen_crossing(C), risk(C,R),
              chosen_fruit(F), weight(F,Wt), D = S + R + Wt.

outcome(safe)    :- support(P), danger(D), P >= D.
outcome(bad_end) :- support(P), danger(D), P < D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("severity", wid, weather.severity))
    for fid, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fid))
        lines.append(asp.fact("weight", fid, fruit.weight))
    for cid, crossing in CROSSINGS.items():
        lines.append(asp.fact("crossing", cid))
        lines.append(asp.fact("max_water", cid, crossing.max_water))
        lines.append(asp.fact("stability", cid, crossing.stability))
        lines.append(asp.fact("risk", cid, crossing.risk))
    for hid, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", hid))
        lines.append(asp.fact("aid", hid, companion.aid))
    for mid, manner in MANNERS.items():
        lines.append(asp.fact("manner", mid))
        lines.append(asp.fact("care", mid, manner.care))
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
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_fruit", params.fruit),
            asp.fact("chosen_crossing", params.crossing),
            asp.fact("chosen_companion", params.companion),
            asp.fact("chosen_manner", params.manner),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a brave child, healing peel, and a dangerous crossing. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--manner", choices=MANNERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.weather and args.crossing:
        weather = WEATHERS[args.weather]
        crossing = CROSSINGS[args.crossing]
        if not crossing_allowed(weather, crossing):
            raise StoryError(explain_rejection(weather, crossing))

    combos = [
        combo
        for combo in valid_combos()
        if (args.weather is None or combo[0] == args.weather)
        and (args.fruit is None or combo[1] == args.fruit)
        and (args.crossing is None or combo[2] == args.crossing)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    weather_id, fruit_id, crossing_id = rng.choice(sorted(combos))
    companion_id = args.companion or rng.choice(sorted(COMPANIONS))
    manner_id = args.manner or rng.choice(sorted(MANNERS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])

    return StoryParams(
        weather=weather_id,
        fruit=fruit_id,
        crossing=crossing_id,
        companion=companion_id,
        manner=manner_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.weather not in WEATHERS:
        raise StoryError(f"(Invalid weather: {params.weather})")
    if params.fruit not in FRUITS:
        raise StoryError(f"(Invalid fruit: {params.fruit})")
    if params.crossing not in CROSSINGS:
        raise StoryError(f"(Invalid crossing: {params.crossing})")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(Invalid companion: {params.companion})")
    if params.manner not in MANNERS:
        raise StoryError(f"(Invalid manner: {params.manner})")
    weather = WEATHERS[params.weather]
    crossing = CROSSINGS[params.crossing]
    if not crossing_allowed(weather, crossing):
        raise StoryError(explain_rejection(weather, crossing))

    world = tell(
        weather=weather,
        fruit=FRUITS[params.fruit],
        crossing=crossing,
        companion_cfg=COMPANIONS[params.companion],
        manner=MANNERS[params.manner],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
    )

    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (weather, fruit, crossing) combos:\n")
        for weather, fruit, crossing in combos:
            print(f"  {weather:6} {fruit:7} {crossing}")
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
            header = (
                f"### {p.child_name}: {p.fruit} peel by {p.crossing} "
                f"({p.weather}, {p.companion}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
