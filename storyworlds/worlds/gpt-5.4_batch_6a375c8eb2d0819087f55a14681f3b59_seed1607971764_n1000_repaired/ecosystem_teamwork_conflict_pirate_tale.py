#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ecosystem_teamwork_conflict_pirate_tale.py
=====================================================================

A standalone story world about children playing pirates by the shore, causing a
small problem in a tide-pool ecosystem, arguing about what to do, and then
working together to fix it.

The central model is simple and state-driven:

    build barrier across a pool channel
        -> pool water grows low and warm
        -> creature becomes distressed
        -> children feel alarm / conflict

    open the channel together
        -> seawater flows back
        -> creature becomes safe again
        -> conflict drops, relief and pride rise

The world refuses combinations that are unreasonable:
- the chosen setting must contain the creature's home habitat
- the chosen setting must offer the material needed for the pirate barrier

The prose follows a pirate-tale shape: pretend-play, a tempting mistake,
conflict, a grown-up explanation using the word "ecosystem", teamwork, and a
bright ending image that proves the children changed what they were doing.

Run it
------
    python storyworlds/worlds/gpt-5.4/ecosystem_teamwork_conflict_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/ecosystem_teamwork_conflict_pirate_tale.py --setting rocky_cove --creature sea_star --barrier rock_wall
    python storyworlds/worlds/gpt-5.4/ecosystem_teamwork_conflict_pirate_tale.py --setting marsh_inlet --creature sea_star
    python storyworlds/worlds/gpt-5.4/ecosystem_teamwork_conflict_pirate_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/ecosystem_teamwork_conflict_pirate_tale.py --verify
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
        female = {"girl", "mother", "aunt", "woman", "ranger_woman"}
        male = {"boy", "father", "uncle", "man", "grandpa", "ranger_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandpa": "grandpa",
            "aunt": "aunt",
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
        }
        return mapping.get(self.type, self.label or self.type)
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
class Setting:
    id: str
    place: str
    scene: str
    detail: str
    habitats: set[str] = field(default_factory=set)
    materials: set[str] = field(default_factory=set)
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
class Creature:
    id: str
    label: str
    the: str
    home: str
    move: str
    safe_image: str
    distress_text: str
    sensitivity: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Barrier:
    id: str
    label: str
    material: str
    build_text: str
    open_text: str
    left_text: str
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
class HelperCfg:
    id: str
    type: str
    arrive: str
    teach: str
    praise: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_trapped_pool(world: World) -> list[str]:
    out: list[str] = []
    barrier = world.get("barrier")
    pool = world.get("pool")
    creature = world.get("creature")
    if barrier.meters["closed"] < THRESHOLD:
        return out
    sig = ("trapped_pool",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pool.meters["water_low"] += 1
    pool.meters["warm"] += 1
    creature.meters["distress"] += float(world.facts["creature_cfg"].sensitivity)
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__distress__")
    return out


def _r_conflict(world: World) -> list[str]:
    a = world.get("instigator")
    b = world.get("cautioner")
    if a.memes["defiance"] < THRESHOLD or b.memes["warning"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    return ["__conflict__"]


def _r_water_returns(world: World) -> list[str]:
    out: list[str] = []
    barrier = world.get("barrier")
    pool = world.get("pool")
    creature = world.get("creature")
    if barrier.meters["open"] < THRESHOLD:
        return out
    sig = ("water_returns",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pool.meters["water_low"] = 0.0
    pool.meters["warm"] = 0.0
    pool.meters["fresh_flow"] += 1
    creature.meters["safe"] += 1
    creature.meters["distress"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["conflict"] = 0.0
    out.append("__saved__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="trapped_pool", tag="physical", apply=_r_trapped_pool),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="water_returns", tag="physical", apply=_r_water_returns),
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


SETTINGS = {
    "rocky_cove": Setting(
        id="rocky_cove",
        place="the rocky cove",
        scene="a wrinkled silver shore full of tide pools",
        detail="Flat rocks made little steps down to the sea, and each pool shone like a pirate's pocket mirror.",
        habitats={"tide_pool", "under_rock"},
        materials={"rocks", "seaweed"},
        tags={"shore", "tide_pool"},
    ),
    "sandy_bay": Setting(
        id="sandy_bay",
        place="the sandy bay",
        scene="a bright beach with a curling line of foam",
        detail="The sand was gold and smooth, with driftwood and tiny pools left behind by the tide.",
        habitats={"tide_pool", "seaweed_patch"},
        materials={"sand", "driftwood"},
        tags={"shore", "beach"},
    ),
    "marsh_inlet": Setting(
        id="marsh_inlet",
        place="the marsh inlet",
        scene="a quiet green edge where the sea whispered through tall grass",
        detail="Thin channels wound between reeds, and glossy seaweed bobbed in the shallows.",
        habitats={"seaweed_patch", "under_rock"},
        materials={"driftwood", "mud"},
        tags={"shore", "marsh"},
    ),
}

CREATURES = {
    "sea_star": Creature(
        id="sea_star",
        label="sea star",
        the="the sea star",
        home="tide_pool",
        move="rested against the wet stone with all five arms spread wide",
        safe_image="lifted one arm, then settled back into the cool water like a little orange star in the sky upside down",
        distress_text="looked dry at the tips and much too still",
        sensitivity=2,
        tags={"sea_star", "ecosystem", "tide_pool"},
    ),
    "hermit_crab": Creature(
        id="hermit_crab",
        label="hermit crab",
        the="the hermit crab",
        home="under_rock",
        move="peeked out of its borrowed shell and made a shy sideways step",
        safe_image="tucked back under the damp rock and left a tiny trail of bubbles behind",
        distress_text="pulled deep into its shell while the puddle around it shrank",
        sensitivity=1,
        tags={"hermit_crab", "ecosystem", "under_rock"},
    ),
    "shore_snail": Creature(
        id="shore_snail",
        label="shore snail",
        the="the shore snail",
        home="seaweed_patch",
        move="clung to a ribbon of green seaweed like a sailor holding a rope",
        safe_image="slid slowly into the swaying green patch and vanished under a soft wave",
        distress_text="sat on the weed above the waterline where the sun could dry it out",
        sensitivity=1,
        tags={"snail", "ecosystem", "seaweed"},
    ),
}

BARRIERS = {
    "rock_wall": Barrier(
        id="rock_wall",
        label="rock wall",
        material="rocks",
        build_text="stacked flat stones across the little channel and called it their pirate harbor gate",
        open_text="lifted the stones away one by one and set them back where the shore had left them",
        left_text="made a fort farther up the beach with dry stones instead",
        tags={"rocks", "barrier"},
    ),
    "driftwood_gate": Barrier(
        id="driftwood_gate",
        label="driftwood gate",
        material="driftwood",
        build_text="laid a fence of driftwood sticks across the trickle and shouted that no ship could pass without treasure",
        open_text="carried the driftwood aside and laid the sticks in a neat pile above the tide line",
        left_text="used the dry driftwood later for a pretend mast on the sand",
        tags={"driftwood", "barrier"},
    ),
    "sand_dam": Barrier(
        id="sand_dam",
        label="sand dam",
        material="sand",
        build_text="patted up a thick sand dam and named the trapped water their secret pirate moat",
        open_text="scooped a gap through the dam until the narrow runnel could breathe again",
        left_text="built their sand fort far from the pool where the tide creatures could be left in peace",
        tags={"sand", "barrier"},
    ),
}

HELPERS = {
    "ranger": HelperCfg(
        id="ranger",
        type="ranger_woman",
        arrive="A beach ranger in a sun hat was walking the shore and heard the shouting.",
        teach='Kneeling beside them, she said, "This little pool is part of an ecosystem. Every plant, rock, and creature belongs to the others, so we must not trap the water for a game."',
        praise="The ranger smiled and told them that helping a small home stay whole was real pirate-sized bravery.",
        tags={"ranger", "ecosystem"},
    ),
    "grandpa": HelperCfg(
        id="grandpa",
        type="grandpa",
        arrive="Grandpa came over with his rolled-up map of the shore and saw the still little pool.",
        teach='He crouched beside them and said, "This is an ecosystem. The moving water, the weed, and the creatures all help one another, so the channel needs to stay open."',
        praise="Grandpa nodded and said they had turned a mistake into good teamwork.",
        tags={"grandpa", "ecosystem"},
    ),
    "aunt": HelperCfg(
        id="aunt",
        type="aunt",
        arrive="Auntie looked up from her shell book and hurried over when she saw them pointing.",
        teach='She touched the wet stones and said, "This pool is an ecosystem. It only works when the sea can reach it, so let us fix it gently together."',
        praise="Auntie squeezed their shoulders and said the shore was safer because they had helped.",
        tags={"aunt", "ecosystem"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "curious", "steady", "thoughtful", "bold", "quick"]


def habitat_phrase(home: str) -> str:
    return {
        "tide_pool": "the cool tide pool",
        "under_rock": "the damp space under a rock",
        "seaweed_patch": "the waving patch of seaweed",
    }[home]


def valid_combo(setting: Setting, creature: Creature, barrier: Barrier) -> bool:
    return creature.home in setting.habitats and barrier.material in setting.materials


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid, creature in CREATURES.items():
            for bid, barrier in BARRIERS.items():
                if valid_combo(setting, creature, barrier):
                    out.append((sid, cid, bid))
    return out


@dataclass
class StoryParams:
    setting: str
    creature: str
    barrier: str
    helper: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    trait: str
    parent_style: str = "pirates"
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


def _do_build_barrier(world: World) -> None:
    world.get("barrier").meters["closed"] += 1
    propagate(world, narrate=False)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    _do_build_barrier(sim)
    return {
        "water_low": sim.get("pool").meters["water_low"] >= THRESHOLD,
        "distress": sim.get("creature").meters["distress"],
    }


def play_setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright low-tide morning, {a.id} and {b.id} scrambled down to {setting.place}. "
        f"They turned the shore into a pirate kingdom, and {setting.detail}"
    )
    world.say(
        f'"Captain {a.id} and Lookout {b.id}!" {a.id} cried. "Let\'s build a harbor for our make-believe ship."'
    )


def discover(world: World, b: Entity, creature: Creature) -> None:
    world.say(
        f"Near their boots, a small pool winked in the sun. Inside, {creature.the} {creature.move}."
    )
    world.say(
        f'{b.id} knelt beside it. "It lives here," {b.pronoun()} whispered.'
    )


def tempt(world: World, a: Entity, barrier: Barrier) -> None:
    a.memes["greed"] += 1
    world.say(
        f"But {a.id} was already busy. {a.pronoun().capitalize()} {barrier.build_text}."
    )
    world.say(
        f'"Now this is our secret harbor," {a.id} said. "No wave gets in unless it pays pirate treasure."'
    )


def warn(world: World, b: Entity, a: Entity, creature: Creature) -> None:
    pred = predict_trouble(world)
    b.memes["warning"] += 1
    world.facts["predicted_distress"] = pred["distress"]
    if pred["water_low"]:
        world.say(
            f'{b.id} looked from the blocked trickle to {creature.the}. '
            f'"{a.id}, the water cannot get back in," {b.pronoun()} said. '
            f'"If we keep it closed, {creature.the} will be stuck."'
        )


def defy(world: World, a: Entity, creature: Creature) -> None:
    a.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"It can be our treasure guard," {a.id} said. "Just for a little while."'
    )


def distress_turn(world: World, creature: Creature) -> None:
    world.say(
        f"But the pool soon changed. The water looked lower, the stones felt warmer, and {creature.the} {creature.distress_text}."
    )
    world.say(
        "That was the moment the game stopped feeling clever."
    )


def helper_arrives(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    world.say(helper_cfg.arrive)
    world.say(helper_cfg.teach)


def teamwork_offer(world: World, helper: Entity, a: Entity, b: Entity, barrier: Barrier) -> None:
    a.memes["shame"] += 1
    b.memes["hope"] += 1
    world.say(
        f'"Can we fix it?" {b.id} asked.'
    )
    world.say(
        f'"Yes," {helper.label_word} said. "You two can work together. One of you lift, and one of you clear the path."'
    )
    world.say(
        f"{a.id} swallowed hard and nodded. {b.id} moved close beside {a.pronoun('object')}."
    )


def repair(world: World, a: Entity, b: Entity, barrier: Barrier) -> None:
    barrier_ent = world.get("barrier")
    barrier_ent.meters["closed"] = 0.0
    barrier_ent.meters["open"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {barrier.open_text}. Their hands were quick now, not bossy."
    )
    world.say(
        "A silver thread of seawater slipped through the channel, then widened and rippled back into the pool."
    )


def saved_image(world: World, creature: Creature, helper_cfg: HelperCfg) -> None:
    world.say(
        f"In the fresh water, {creature.the} stirred and {creature.safe_image}."
    )
    world.say(helper_cfg.praise)


def ending(world: World, a: Entity, b: Entity, barrier: Barrier, setting: Setting) -> None:
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f'"No more pirate harbors across living pools," {a.id} said quietly.'
    )
    world.say(
        f'{b.id} smiled. "We can still be pirates. We just have to be kind pirates."'
    )
    world.say(
        f"So they {barrier.left_text}, and this time they left the little channel open."
    )
    world.say(
        f"When they ran off across {setting.place}, their flag flew high, and behind them the tiny shore home stayed bright, wet, and alive."
    )


def tell(
    setting: Setting,
    creature_cfg: Creature,
    barrier_cfg: Barrier,
    helper_cfg: HelperCfg,
    instigator_name: str,
    instigator_gender: str,
    cautioner_name: str,
    cautioner_gender: str,
    trait: str,
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator_name,
        role="instigator",
        traits=["bold"],
        attrs={"name": instigator_name},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner_name,
        role="cautioner",
        traits=[trait],
        attrs={"name": cautioner_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.id,
        role="helper",
        attrs={},
    ))
    pool = world.add(Entity(
        id="pool",
        type="pool",
        label="pool",
        attrs={"home": creature_cfg.home},
    ))
    creature = world.add(Entity(
        id="creature",
        type="creature",
        label=creature_cfg.label,
        attrs={"home": creature_cfg.home},
    ))
    barrier = world.add(Entity(
        id="barrier",
        type="barrier",
        label=barrier_cfg.label,
        attrs={"material": barrier_cfg.material},
    ))
    world.facts.update(
        setting=setting,
        creature_cfg=creature_cfg,
        barrier_cfg=barrier_cfg,
        helper_cfg=helper_cfg,
        predicted_distress=0.0,
    )

    play_setup(world, a, b, setting)
    discover(world, b, creature_cfg)

    world.para()
    tempt(world, a, barrier_cfg)
    warn(world, b, a, creature_cfg)
    _do_build_barrier(world)
    defy(world, a, creature_cfg)
    distress_turn(world, creature_cfg)

    world.para()
    helper_arrives(world, helper, helper_cfg)
    teamwork_offer(world, helper, a, b, barrier_cfg)
    repair(world, a, b, barrier_cfg)
    saved_image(world, creature_cfg, helper_cfg)

    world.para()
    ending(world, a, b, barrier_cfg, setting)

    world.facts.update(
        instigator=a,
        cautioner=b,
        helper=helper,
        pool=pool,
        creature=creature,
        barrier=barrier,
        rescued=creature.meters["safe"] >= THRESHOLD,
        conflict_happened=a.memes["defiance"] >= THRESHOLD and b.memes["warning"] >= THRESHOLD,
        teamwork=a.memes["teamwork"] >= THRESHOLD and b.memes["teamwork"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ecosystem": [
        (
            "What is an ecosystem?",
            "An ecosystem is a living neighborhood where water, plants, animals, and rocks all affect one another. When one part is disturbed, the other parts can be disturbed too.",
        )
    ],
    "tide_pool": [
        (
            "What is a tide pool?",
            "A tide pool is a little pocket of seawater left behind when the tide goes out. Small sea creatures can live there until the sea returns.",
        )
    ],
    "sea_star": [
        (
            "Why should a sea star stay in the water?",
            "A sea star needs cool seawater around it. If it is left too warm and dry, it can become weak.",
        )
    ],
    "hermit_crab": [
        (
            "Why do hermit crabs hide under rocks?",
            "Hermit crabs use shady, damp places for safety. The rock helps keep them cooler and hidden from danger.",
        )
    ],
    "snail": [
        (
            "Why does seaweed matter to a shore snail?",
            "Seaweed gives a shore snail a wet place to cling and hide. It is part of the snail's small home.",
        )
    ],
    "shore": [
        (
            "Why should children be gentle at the shore?",
            "The shore can look like a playground, but many tiny animals live there. Gentle hands and careful feet help keep their homes safe.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help one another on the same job instead of pulling against each other. Working together often fixes a problem faster and more kindly.",
        )
    ],
    "ranger": [
        (
            "What does a beach ranger do?",
            "A beach ranger helps look after the shore and teaches people how to keep it safe. Rangers know a lot about animals, plants, and habitats.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ecosystem", "tide_pool", "sea_star", "hermit_crab", "snail", "shore", "teamwork", "ranger"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    creature = f["creature_cfg"]
    barrier = f["barrier_cfg"]
    setting = f["setting"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the word "ecosystem" and takes place at {setting.place}.',
        f"Tell a story where two children pretend to be pirates, argue after building a {barrier.label}, and then work together to help {creature.the}.",
        f"Write a gentle shore adventure where {a.label} and {b.label} learn that play must make room for a tiny sea home.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    return "a boy and a girl"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    creature_cfg = f["creature_cfg"]
    setting = f["setting"]
    barrier_cfg = f["barrier_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.label} and {b.label}, who were playing pirates at {setting.place}. It is also about a helpful {helper.label_word} and {creature_cfg.the} they noticed in the little pool.",
        ),
        (
            "What problem did the children cause?",
            f"They built a {barrier_cfg.label} across the small channel feeding the pool. That trapped the water and left {creature_cfg.the} in a warmer, lower puddle instead of the moving sea.",
        ),
        (
            f"Why did {b.label} worry about {creature_cfg.the}?",
            f"{b.label} could see the water could not get back in once the channel was blocked. That meant {creature_cfg.the} might be stuck and unsafe in its tiny home.",
        ),
        (
            "What did the grown-up mean by saying the pool was part of an ecosystem?",
            "The grown-up meant the water, plants, rocks, and little creature all belonged together in one living system. When the children blocked the channel for their game, they disturbed more than one small thing at once.",
        ),
        (
            "How did the children fix the problem?",
            f"They worked together to open the channel again and let fresh seawater return. Because they stopped arguing and shared the job, {creature_cfg.the} could settle safely back into its home.",
        ),
        (
            "How did the story end?",
            f"It ended with the children still playing pirates, but in a kinder way. They moved their fort away from the living pool and left the tiny shore home bright, wet, and alive behind them.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ecosystem", "shore", "teamwork"}
    tags |= set(f["setting"].tags)
    tags |= set(f["creature_cfg"].tags)
    tags |= set(f["helper_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        label = e.label if e.label else e.id
        lines.append(f"  {e.id:10} ({e.type:12}) {label} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="rocky_cove",
        creature="sea_star",
        barrier="rock_wall",
        helper="ranger",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        trait="careful",
    ),
    StoryParams(
        setting="sandy_bay",
        creature="shore_snail",
        barrier="driftwood_gate",
        helper="aunt",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        trait="thoughtful",
    ),
    StoryParams(
        setting="sandy_bay",
        creature="sea_star",
        barrier="sand_dam",
        helper="grandpa",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        trait="steady",
    ),
    StoryParams(
        setting="marsh_inlet",
        creature="shore_snail",
        barrier="driftwood_gate",
        helper="ranger",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        trait="curious",
    ),
    StoryParams(
        setting="rocky_cove",
        creature="hermit_crab",
        barrier="rock_wall",
        helper="grandpa",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        trait="careful",
    ),
]


def explain_rejection(setting: Setting, creature: Creature, barrier: Barrier) -> str:
    if creature.home not in setting.habitats:
        return (
            f"(No story: {creature.the} belongs in {habitat_phrase(creature.home)}, "
            f"but {setting.place} does not offer that habitat. Pick a creature whose home fits the setting.)"
        )
    if barrier.material not in setting.materials:
        return (
            f"(No story: a {barrier.label} needs {barrier.material}, but {setting.place} does not naturally offer that material for the children to build with.)"
        )
    return "(No story: this combination does not make a reasonable shore problem.)"


ASP_RULES = r"""
valid(S, C, B) :- setting(S), creature(C), barrier(B),
                  creature_home(C, H), habitat(S, H),
                  barrier_material(B, M), material(S, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for h in sorted(setting.habitats):
            lines.append(asp.fact("habitat", sid, h))
        for m in sorted(setting.materials):
            lines.append(asp.fact("material", sid, m))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("creature_home", cid, creature.home))
    for bid, barrier in BARRIERS.items():
        lines.append(asp.fact("barrier", bid))
        lines.append(asp.fact("barrier_material", bid, barrier.material))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    emit(sample, trace=False, qa=False)


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        _smoke_generate()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(777))
        params.seed = 777
        sample = generate(params)
        if not sample.story or not sample.story_qa or not sample.world_qa:
            raise StoryError("resolved default story was missing story or QA output")
        print("OK: default resolve_params() path generated story and QA.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirate play, ecosystem trouble, conflict, and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--barrier", choices=BARRIERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.creature and args.barrier:
        setting = SETTINGS[args.setting]
        creature = CREATURES[args.creature]
        barrier = BARRIERS[args.barrier]
        if not valid_combo(setting, creature, barrier):
            raise StoryError(explain_rejection(setting, creature, barrier))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.creature is None or combo[1] == args.creature)
        and (args.barrier is None or combo[2] == args.barrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, creature_id, barrier_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        creature=creature_id,
        barrier=barrier_id,
        helper=helper_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        creature = CREATURES[params.creature]
        barrier = BARRIERS[params.barrier]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(No story: unknown option {err.args[0]!r}.)") from None

    if not valid_combo(setting, creature, barrier):
        raise StoryError(explain_rejection(setting, creature, barrier))

    world = tell(
        setting=setting,
        creature_cfg=creature,
        barrier_cfg=barrier,
        helper_cfg=helper,
        instigator_name=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner_name=params.cautioner,
        cautioner_gender=params.cautioner_gender,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, creature, barrier) combos:\n")
        for setting, creature, barrier in combos:
            print(f"  {setting:12} {creature:12} {barrier}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.creature} at {p.setting} ({p.barrier})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
