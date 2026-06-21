#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py
===================================================

A standalone story world in a fairy-tale style. A small fairy and a magical
creature are hurrying toward a moonlit celebration when the creature's magic
gland stops working properly. The fairy must choose a remedy that actually fits
the trouble: a rinsing cure for soot, a warming cure for frost, or a gentle
combing cure for a burr.

The world model enforces that the problem and cure must match. A glow-snail can
have soot or frost on its lamp gland; a perfume moth can have a burr or frost
near its scent gland; a bell frog can have soot or a burr around its song
gland. A bad match is rejected on purpose, because the story's turn should come
from a sensible magical fix rather than arbitrary wording.

Run it
------
    python storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py --creature glow_snail --problem soot --remedy moonwater
    python storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py --creature glow_snail --problem soot --remedy ember_cloak
    python storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py --json
    python storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py --asp
    python storyworlds/worlds/gpt-5.4/gland_magic_fairy_tale.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy_girl", "woman", "grandmother"}
        male = {"boy", "man", "owl"}
        if self.type in female:
            table = {"subject": "she", "object": "her", "possessive": "her"}
            return table[case]
        if self.type in male:
            table = {"subject": "he", "object": "him", "possessive": "his"}
            return table[case]
        table = {"subject": "it", "object": "it", "possessive": "its"}
        return table[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")
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
    opening: str
    closing: str
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
class CreatureCfg:
    id: str
    label: str
    type: str
    gland_name: str
    magic_noun: str
    magic_verb: str
    gift_sentence: str
    ending_image: str
    problems: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    label: str
    meter: str
    need: str
    severity: int
    cause: str
    symptom: str
    warning: str
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
    label: str
    phrase: str
    need: str
    speed: int
    action: str
    helper_line: str
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
class HelperCfg:
    id: str
    label: str
    type: str
    arrival: str
    wisdom: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

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


def _r_trouble(world: World) -> list[str]:
    creature = world.get("creature")
    place = world.get("place")
    meter = world.facts["problem_meter"]
    sig = ("trouble", meter)
    if creature.meters[meter] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["magic_faded"] += 1
    creature.memes["worry"] += 1
    world.get("fairy").memes["care"] += 1
    place.meters["dim"] += 1
    return ["__trouble__"]


def _r_restore(world: World) -> list[str]:
    creature = world.get("creature")
    place = world.get("place")
    problem_meter = world.facts["problem_meter"]
    need_meter = world.facts["need_meter"]
    sig = ("restore", problem_meter, need_meter)
    if creature.meters[problem_meter] < THRESHOLD:
        return []
    if creature.meters[need_meter] < THRESHOLD:
        return []
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["magic_faded"] = 0.0
    creature.meters["magic_restored"] += 1
    creature.memes["relief"] += 1
    creature.memes["hope"] += 1
    world.get("fairy").memes["joy"] += 1
    place.meters["dim"] = 0.0
    return ["__restore__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="trouble", tag="physical", apply=_r_trouble),
    Rule(name="restore", tag="physical", apply=_r_restore),
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
                produced.extend(line for line in lines if not line.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def compatible(creature: CreatureCfg, problem: Problem, remedy: Remedy) -> bool:
    return problem.id in creature.problems and problem.need == remedy.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for creature_id, creature in CREATURES.items():
        for problem_id, problem in PROBLEMS.items():
            for remedy_id, remedy in REMEDIES.items():
                if compatible(creature, problem, remedy):
                    combos.append((creature_id, problem_id, remedy_id))
    return combos


def restored_in_time(problem: Problem, remedy: Remedy, delay: int) -> bool:
    return remedy.speed >= problem.severity + delay


def predict_without_help(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "dim": sim.get("place").meters["dim"] >= THRESHOLD,
        "magic_faded": sim.get("creature").meters["magic_faded"] >= THRESHOLD,
    }


def introduce(world: World, fairy: Entity, creature: Entity, place: Place, creature_cfg: CreatureCfg) -> None:
    world.say(
        f"In {place.label}, where {place.opening}, lived a small fairy named {fairy.id}."
    )
    world.say(
        f"{fairy.id} was kind and quick, and {creature.label} was {fairy.pronoun('possessive')} dear friend. "
        f"{creature_cfg.gift_sentence}"
    )
    world.say(
        f"That evening they were hurrying toward the Moon-Thread Feast, because the feast began best when "
        f"{creature.label} could {creature_cfg.magic_verb}."
    )


def mishap(world: World, fairy: Entity, creature: Entity, creature_cfg: CreatureCfg, problem: Problem) -> None:
    creature.meters[problem.meter] += 1
    world.say(
        f"But under a silver fern, {problem.cause}. At once, {creature.label}'s {creature_cfg.gland_name} grew troubled."
    )
    propagate(world, narrate=False)
    world.say(problem.symptom)


def warning(world: World, fairy: Entity, creature: Entity, creature_cfg: CreatureCfg, problem: Problem) -> None:
    forecast = predict_without_help(world)
    world.facts["predicted_dim"] = forecast["dim"]
    extra = ""
    if forecast["dim"]:
        extra = f" If they did nothing, {problem.warning}"
    world.say(
        f'{fairy.id} laid a little hand on {creature.label} and whispered, '
        f'"Your {creature_cfg.gland_name} is not making its {creature_cfg.magic_noun} properly.{extra}"'
    )


def call_helper(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    world.say(
        f"Just then {helper_cfg.arrival}, and {helper.label} came softly near."
    )
    world.say(
        f'{helper.label.capitalize()} listened and said, "{helper_cfg.wisdom}"'
    )


def apply_remedy(world: World, fairy: Entity, creature: Entity, creature_cfg: CreatureCfg, remedy: Remedy) -> None:
    creature.meters[remedy.need] += 1
    creature.memes["hope"] += 1
    fairy.memes["bravery"] += 1
    world.say(remedy.action.format(fairy=fairy.id, creature=creature.label, gland=creature_cfg.gland_name))
    propagate(world, narrate=False)


def timely_ending(world: World, fairy: Entity, creature: Entity, creature_cfg: CreatureCfg, place: Place) -> None:
    fairy.memes["joy"] += 1
    creature.memes["joy"] += 1
    world.say(
        f"Soon the {creature_cfg.gland_name} stirred, and {creature.label} filled the path with {creature_cfg.magic_noun}."
    )
    world.say(
        f"They reached the Moon-Thread Feast before the first ribbon of moonlight touched the stones, and everyone clapped to see the magic return."
    )
    world.say(
        f"After that, {creature_cfg.ending_image} In {place.label}, the night no longer felt uncertain at all."
    )


def late_ending(world: World, fairy: Entity, creature: Entity, creature_cfg: CreatureCfg, place: Place) -> None:
    fairy.memes["steady"] += 1
    world.say(
        f"The remedy worked, but slowly. The first bell of the feast rang while the path was still dim, so {fairy.id} led the way with a tiny star-seed lamp cupped in both hands."
    )
    world.say(
        f"Then, just past the last briar arch, {creature.label}'s {creature_cfg.gland_name} woke at last and spilled out {creature_cfg.magic_noun}."
    )
    world.say(
        f"They arrived a little late, yet the feast grew brighter when they came, and on the way home {creature.label} used that fresh magic to help two lost field mice find their burrow. {place.closing}"
    )


def tell(
    place: Place,
    creature_cfg: CreatureCfg,
    problem: Problem,
    remedy: Remedy,
    helper_cfg: HelperCfg,
    fairy_name: str = "Lina",
    fairy_type: str = "fairy_girl",
    delay: int = 0,
) -> World:
    world = World(place=place)
    world.facts["problem_meter"] = problem.meter
    world.facts["need_meter"] = remedy.need
    world.facts["delay"] = delay

    fairy = world.add(
        Entity(
            id=fairy_name,
            kind="character",
            type=fairy_type,
            label=fairy_name,
            role="fairy",
            traits=["kind", "brave"],
            attrs={"delay": delay},
            tags={"fairy", "magic"},
        )
    )
    creature = world.add(
        Entity(
            id="creature",
            kind="character",
            type=creature_cfg.type,
            label=creature_cfg.label,
            role="creature",
            traits=["gentle"],
            attrs={"gland_name": creature_cfg.gland_name},
            tags=set(creature_cfg.tags),
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            role="helper",
            traits=["wise"],
            attrs={},
            tags=set(helper_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=place.label,
            role="place",
            traits=[],
            attrs={},
            tags=set(place.tags),
        )
    )

    introduce(world=world, fairy=fairy, creature=creature, place=place, creature_cfg=creature_cfg)

    world.para()
    mishap(world=world, fairy=fairy, creature=creature, creature_cfg=creature_cfg, problem=problem)
    warning(world=world, fairy=fairy, creature=creature, creature_cfg=creature_cfg, problem=problem)

    world.para()
    call_helper(world=world, helper=helper, helper_cfg=helper_cfg)
    world.say(remedy.helper_line.format(helper=helper.label, creature=creature.label, gland=creature_cfg.gland_name))
    apply_remedy(world=world, fairy=fairy, creature=creature, creature_cfg=creature_cfg, remedy=remedy)

    world.para()
    outcome = "timely" if restored_in_time(problem=problem, remedy=remedy, delay=delay) else "late"
    if outcome == "timely":
        timely_ending(world=world, fairy=fairy, creature=creature, creature_cfg=creature_cfg, place=place)
    else:
        late_ending(world=world, fairy=fairy, creature=creature, creature_cfg=creature_cfg, place=place)

    world.facts.update(
        fairy=fairy,
        creature=creature,
        helper=helper,
        place_cfg=place,
        creature_cfg=creature_cfg,
        problem_cfg=problem,
        remedy_cfg=remedy,
        gland_name=creature_cfg.gland_name,
        magic_noun=creature_cfg.magic_noun,
        outcome=outcome,
        restored=creature.meters["magic_restored"] >= THRESHOLD,
        feast_dimmed_before_fix=outcome == "late",
    )
    return world


PLACES = {
    "moon_meadow": Place(
        id="moon_meadow",
        label="the Moon Meadow",
        opening="dew pearls hung from every blade of grass like tiny lanterns",
        closing="When they looked back, the meadow shimmered as if the moon itself had smiled.",
        tags={"meadow", "moon", "magic"},
    ),
    "crystal_pond": Place(
        id="crystal_pond",
        label="the Crystal Pond",
        opening="the reeds whispered and the water kept little stars on its dark skin",
        closing="The pond held their reflections in bright pieces, like a bowl full of wishes.",
        tags={"pond", "moon", "magic"},
    ),
    "briar_bridge": Place(
        id="briar_bridge",
        label="the Briar Bridge",
        opening="pale roses climbed the rails and glowed whenever a kind word was spoken",
        closing="Behind them the roses stayed open, drinking in the last of the magic glow.",
        tags={"bridge", "magic"},
    ),
}

CREATURES = {
    "glow_snail": CreatureCfg(
        id="glow_snail",
        label="the glow-snail",
        type="snail",
        gland_name="lamp gland",
        magic_noun="a warm golden glow",
        magic_verb="shine a clear path through the dark grass",
        gift_sentence="When its lamp gland was healthy, it could shine a clear path through the dark grass for anyone walking late",
        ending_image="the glow-snail glided ahead like a living lantern, and even the shy crickets came out to watch.",
        problems={"soot", "frost"},
        tags={"glow_snail", "gland", "light"},
    ),
    "perfume_moth": CreatureCfg(
        id="perfume_moth",
        label="the perfume moth",
        type="moth",
        gland_name="scent gland",
        magic_noun="a sweet silver perfume",
        magic_verb="wake sleeping blossoms with a sweet silver perfume",
        gift_sentence="When its scent gland was healthy, it could wake sleeping blossoms with a sweet silver perfume",
        ending_image="the perfume moth drifted above the flowers, and one by one the petals opened like little cups of milk.",
        problems={"burr", "frost"},
        tags={"perfume_moth", "gland", "flowers"},
    ),
    "bell_frog": CreatureCfg(
        id="bell_frog",
        label="the bell frog",
        type="frog",
        gland_name="song gland",
        magic_noun="a ring of silver notes",
        magic_verb="send a ring of silver notes over the marsh",
        gift_sentence="When its song gland was healthy, it could send a ring of silver notes over the marsh and make the lanterns bob in time",
        ending_image="the bell frog sat on a smooth stone, singing so brightly that the lantern strings trembled with joy.",
        problems={"soot", "burr"},
        tags={"bell_frog", "gland", "song"},
    ),
}

PROBLEMS = {
    "soot": Problem(
        id="soot",
        label="soot",
        meter="soot",
        need="rinse",
        severity=1,
        cause="a sleepy puff of chimney smoke rolled down from the old hill tower and smudged the gland with soot",
        symptom="The magic came out in weak little sputters, and the shadows under the leaves suddenly seemed much deeper.",
        warning="the path to the feast would stay dim, and small feet might stumble",
        tags={"soot", "cleaning", "gland"},
    ),
    "frost": Problem(
        id="frost",
        label="frost",
        meter="frost",
        need="warmth",
        severity=2,
        cause="a stray frost-sprite kissed the gland and left it numb and cold",
        symptom="No proper magic came at all, only a tiny shiver, and the creature looked frightened by its own silence.",
        warning="the feast would begin in a hush instead of magic",
        tags={"frost", "warmth", "gland"},
    ),
    "burr": Problem(
        id="burr",
        label="burr",
        meter="burr",
        need="comb",
        severity=2,
        cause="a hooked moon-burr caught against the gland and would not let go",
        symptom="Every time the creature tried to make magic, it winced, and the spell tangled before it could bloom.",
        warning="the magic would stay knotted and sore",
        tags={"burr", "care", "gland"},
    ),
}

REMEDIES = {
    "moonwater": Remedy(
        id="moonwater",
        label="moonwater rinse",
        phrase="a moonwater rinse",
        need="rinse",
        speed=2,
        action="{fairy} dipped a thimble into a moonwater pool and washed the soot away from {creature}'s {gland} with three patient circles.",
        helper_line="\"Use a moonwater rinse,\" said {helper}. \"That cure is gentle and clear, and it will wake the magic without hurting the {gland}.\"",
        tags={"moonwater", "magic", "cleaning"},
    ),
    "ember_cloak": Remedy(
        id="ember_cloak",
        label="ember-cloak wrap",
        phrase="an ember-cloak wrap",
        need="warmth",
        speed=3,
        action="{fairy} wrapped {creature} in a fold of ember-cloth so soft and warm that the chill around the {gland} slowly melted away.",
        helper_line="\"Warmth is needed,\" said {helper}. \"An ember-cloak wrap will coax the frozen magic back, drop by glowing drop.\"",
        tags={"warmth", "magic", "ember_cloak"},
    ),
    "silver_comb": Remedy(
        id="silver_comb",
        label="silver-comb brushing",
        phrase="a silver-comb brushing",
        need="comb",
        speed=1,
        action="{fairy} took a silver comb no bigger than a leaf and teased the burr loose from {creature}'s {gland} one shining tooth at a time.",
        helper_line="\"Do not pull,\" said {helper}. \"A silver-comb brushing is the right kindness for a snagged gland.\"",
        tags={"silver_comb", "care", "magic"},
    ),
}

HELPERS = {
    "owl": HelperCfg(
        id="owl",
        label="the old owl",
        type="owl",
        arrival="a pair of round golden eyes blinked from a willow hollow",
        wisdom="Moonlit troubles yield best to calm hands and the right little spell",
        tags={"owl", "wisdom"},
    ),
    "grandmother_willow": HelperCfg(
        id="grandmother_willow",
        label="Grandmother Willow",
        type="grandmother",
        arrival="the willow branches rustled though there was no wind at all",
        wisdom="Magic is shy when it is sore, but it returns when someone is gentle and true",
        tags={"willow", "wisdom"},
    ),
    "spider_tailor": HelperCfg(
        id="spider_tailor",
        label="the spider tailor",
        type="spider",
        arrival="a silk ladder dropped from a branch, bright as spun frost",
        wisdom="Even the smallest tangle can be mended, if one works by moonlight and does not hurry the thread",
        tags={"spider", "wisdom"},
    ),
}

FAIRY_NAMES = ["Lina", "Mira", "Poppy", "Tansy", "Nella", "Wren", "Ivy", "Della"]


@dataclass
class StoryParams:
    place: str
    creature: str
    problem: str
    remedy: str
    helper: str
    fairy_name: str
    fairy_type: str = "fairy_girl"
    delay: int = 0
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
    "gland": [
        (
            "What is a gland?",
            "A gland is a part of a body that makes or gives out something. In this fairy tale, the creature's magic gland is the little place where its special magic comes from.",
        )
    ],
    "moonwater": [
        (
            "What is moonwater in a fairy tale?",
            "Moonwater is magical water that has rested under moonlight. In stories, it can wash something gently and help a spell feel clear again.",
        )
    ],
    "warmth": [
        (
            "Why can warmth help after frost?",
            "Frost makes things cold and stiff. Gentle warmth helps them loosen and wake up again.",
        )
    ],
    "silver_comb": [
        (
            "Why use a comb on a burr instead of pulling hard?",
            "A comb can lift a burr out slowly without hurting tender skin. Pulling hard can make the sore spot worse.",
        )
    ],
    "soot": [
        (
            "What is soot?",
            "Soot is a soft black dirt made by smoke and fire. It can smudge things and clog tiny openings.",
        )
    ],
    "frost": [
        (
            "What does frost do?",
            "Frost is a thin layer of ice-cold crystals. It can make something feel numb, cold, and slow.",
        )
    ],
    "burr": [
        (
            "What is a burr?",
            "A burr is a prickly little seed that can catch on fur, cloth, or feathers. It sticks easily and can be hard to remove.",
        )
    ],
    "light": [
        (
            "Why does light help on a dark path?",
            "Light helps you see where to put your feet. It also makes a place feel less scary because the shadows are not hiding everything.",
        )
    ],
    "flowers": [
        (
            "Why do flowers matter in fairy tales?",
            "Flowers often show that a place is alive, peaceful, and full of magic. When they open, it can mean that hope has returned.",
        )
    ],
    "song": [
        (
            "How can a song change a mood?",
            "A bright song can make people feel calmer and happier. It gathers everyone into the same happy moment.",
        )
    ],
    "owl": [
        (
            "Why is an owl often wise in stories?",
            "Owls are quiet and watchful, so fairy tales often make them wise helpers. They seem to notice what others miss.",
        )
    ],
    "willow": [
        (
            "Why might a willow tree feel magical in a fairy tale?",
            "A willow has long, whispering branches that seem to listen and remember. That makes it a lovely tree for gentle old magic.",
        )
    ],
    "spider": [
        (
            "Why can a spider be a good helper in a fairy tale?",
            "A spider is patient and careful with fine threads. That makes a spider a good mender of tiny tangles in story magic.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "gland",
    "soot",
    "frost",
    "burr",
    "moonwater",
    "warmth",
    "silver_comb",
    "light",
    "flowers",
    "song",
    "owl",
    "willow",
    "spider",
]


def generation_prompts(world: World) -> list[str]:
    fairy = world.facts["fairy"]
    creature_cfg = world.facts["creature_cfg"]
    problem = world.facts["problem_cfg"]
    remedy = world.facts["remedy_cfg"]
    outcome = world.facts["outcome"]
    finish = "arrives in time for a moonlit feast" if outcome == "timely" else "arrives late but still brings help and light"
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the word "gland" and magical problem-solving.',
        f"Tell a gentle fairy story where {fairy.id} helps {creature_cfg.label} after {problem.label} troubles its {creature_cfg.gland_name}, and the right cure is {remedy.phrase}.",
        f"Write a moonlit tale in which a small magical creature loses its special gift for a while, then {finish}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    fairy = world.facts["fairy"]
    creature = world.facts["creature"]
    creature_cfg = world.facts["creature_cfg"]
    problem = world.facts["problem_cfg"]
    remedy = world.facts["remedy_cfg"]
    helper = world.facts["helper"]
    place = world.facts["place_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a small fairy named {fairy.id} and {creature.label}. They were hurrying through {place.label} toward the Moon-Thread Feast together.",
        ),
        (
            f"What special magic did {creature.label} usually make?",
            f"{creature.label.capitalize()} usually made {creature_cfg.magic_noun}. That magic mattered because it helped {creature_cfg.magic_verb}.",
        ),
        (
            f"What went wrong with {creature.label}'s {creature_cfg.gland_name}?",
            f"{problem.cause[0].upper()}{problem.cause[1:]}. After that, {problem.symptom.lower()}",
        ),
        (
            f"Why did {fairy.id} worry?",
            f"{fairy.id} worried because the creature's magic had faded and the way ahead might stay dim or troubled. If they did nothing, {problem.warning}.",
        ),
        (
            f"How did {helper.label} help?",
            f"{helper.label.capitalize()} listened calmly and chose the right kind of cure. {remedy.helper_line.format(helper=helper.label, creature=creature.label, gland=creature_cfg.gland_name).strip('\"')}",
        ),
        (
            f"Why was {remedy.phrase} the right remedy?",
            f"It matched the real problem instead of being guessed at. {problem.label.capitalize()} needed {problem.need}, and {remedy.phrase} gave exactly that kind of help.",
        ),
    ]
    if outcome == "timely":
        qa.append(
            (
                "How did the story end?",
                f"It ended happily and on time. {creature.label.capitalize()} recovered before the feast began and filled the path with {creature_cfg.magic_noun}.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended a little late, but still warmly. The cure worked slowly, so {fairy.id} guided the way first, and then {creature.label}'s magic returned and helped others on the way home.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    creature_cfg = world.facts["creature_cfg"]
    problem = world.facts["problem_cfg"]
    remedy = world.facts["remedy_cfg"]
    helper = world.facts["helper"]
    tags = {"gland"} | set(problem.tags) | set(remedy.tags) | set(helper.tags) | set(creature_cfg.tags)
    if "light" in creature_cfg.tags:
        tags.add("light")
    if "flowers" in creature_cfg.tags:
        tags.add("flowers")
    if "song" in creature_cfg.tags:
        tags.add("song")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_meadow",
        creature="glow_snail",
        problem="soot",
        remedy="moonwater",
        helper="owl",
        fairy_name="Lina",
        fairy_type="fairy_girl",
        delay=0,
    ),
    StoryParams(
        place="crystal_pond",
        creature="perfume_moth",
        problem="frost",
        remedy="ember_cloak",
        helper="grandmother_willow",
        fairy_name="Mira",
        fairy_type="fairy_girl",
        delay=0,
    ),
    StoryParams(
        place="briar_bridge",
        creature="bell_frog",
        problem="burr",
        remedy="silver_comb",
        helper="spider_tailor",
        fairy_name="Poppy",
        fairy_type="fairy_girl",
        delay=2,
    ),
    StoryParams(
        place="crystal_pond",
        creature="perfume_moth",
        problem="burr",
        remedy="silver_comb",
        helper="owl",
        fairy_name="Ivy",
        fairy_type="fairy_girl",
        delay=1,
    ),
    StoryParams(
        place="moon_meadow",
        creature="glow_snail",
        problem="frost",
        remedy="ember_cloak",
        helper="grandmother_willow",
        fairy_name="Nella",
        fairy_type="fairy_girl",
        delay=1,
    ),
]


def explain_rejection(creature: CreatureCfg, problem: Problem, remedy: Remedy) -> str:
    if problem.id not in creature.problems:
        choices = ", ".join(sorted(creature.problems))
        return (
            f"(No story: {creature.label}'s {creature.gland_name} is not the kind that gets '{problem.id}' trouble here. "
            f"Try one of: {choices}.)"
        )
    return (
        f"(No story: {problem.id} needs a remedy that provides '{problem.need}', but {remedy.id} provides '{remedy.need}'. "
        f"Pick the cure that truly fits the gland trouble.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "timely" if restored_in_time(PROBLEMS[params.problem], REMEDIES[params.remedy], params.delay) else "late"


ASP_RULES = r"""
% --- compatible stories ----------------------------------------------------
valid(C, P, R) :- creature(C), problem(P), remedy(R), suffers(C, P), needs(P, N), provides(R, N).

% --- timing model ----------------------------------------------------------
effort(S + D) :- chosen_problem(P), severity(P, S), delay(D).
timely :- chosen_remedy(R), speed(R, Sp), effort(E), Sp >= E.
outcome(timely) :- timely.
outcome(late)   :- not timely.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        for problem in sorted(creature.problems):
            lines.append(asp.fact("suffers", creature_id, problem))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.need))
        lines.append(asp.fact("severity", problem_id, problem.severity))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("provides", remedy_id, remedy.need))
        lines.append(asp.fact("speed", remedy_id, remedy.speed))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("Smoke test generation produced empty story.")
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a magic gland, the right remedy, and a moonlit ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--fairy-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="How much time is lost before the cure is finished.")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.problem and args.remedy:
        creature = CREATURES[args.creature]
        problem = PROBLEMS[args.problem]
        remedy = REMEDIES[args.remedy]
        if not compatible(creature, problem, remedy):
            raise StoryError(explain_rejection(creature, problem, remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.creature is None or combo[0] == args.creature)
        and (args.problem is None or combo[1] == args.problem)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    creature_id, problem_id, remedy_id = rng.choice(sorted(combos))
    place_id = args.place or rng.choice(sorted(PLACES))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    fairy_name = args.fairy_name or rng.choice(FAIRY_NAMES)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        place=place_id,
        creature=creature_id,
        problem=problem_id,
        remedy=remedy_id,
        helper=helper_id,
        fairy_name=fairy_name,
        fairy_type="fairy_girl",
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    creature = CREATURES[params.creature]
    problem = PROBLEMS[params.problem]
    remedy = REMEDIES[params.remedy]
    if not compatible(creature, problem, remedy):
        raise StoryError(explain_rejection(creature, problem, remedy))

    world = tell(
        place=PLACES[params.place],
        creature_cfg=creature,
        problem=problem,
        remedy=remedy,
        helper_cfg=HELPERS[params.helper],
        fairy_name=params.fairy_name,
        fairy_type=params.fairy_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (creature, problem, remedy) triples:\n")
        for creature, problem, remedy in combos:
            print(f"  {creature:13} {problem:7} {remedy}")
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
            header = f"### {p.fairy_name}: {p.creature} / {p.problem} / {p.remedy} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
