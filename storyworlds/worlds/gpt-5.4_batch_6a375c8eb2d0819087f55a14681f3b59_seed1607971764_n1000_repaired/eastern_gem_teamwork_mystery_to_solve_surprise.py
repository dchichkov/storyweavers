#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/eastern_gem_teamwork_mystery_to_solve_surprise.py
==============================================================================

A standalone storyworld for a small folk-tale domain:
in an eastern village, a festival gem goes missing, two children work together
to solve the mystery, and the ending includes both the true explanation and a
gentle surprise.

Run it
------
    python storyworlds/worlds/gpt-5.4/eastern_gem_teamwork_mystery_to_solve_surprise.py
    python storyworlds/worlds/gpt-5.4/eastern_gem_teamwork_mystery_to_solve_surprise.py --setting harbor --clue feather
    python storyworlds/worlds/gpt-5.4/eastern_gem_teamwork_mystery_to_solve_surprise.py --hiding reed_bank --method ladder
    python storyworlds/worlds/gpt-5.4/eastern_gem_teamwork_mystery_to_solve_surprise.py --all
    python storyworlds/worlds/gpt-5.4/eastern_gem_teamwork_mystery_to_solve_surprise.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/eastern_gem_teamwork_mystery_to_solve_surprise.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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
SENSE_MIN = 2


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
        female = {"girl", "woman", "grandmother"}
        male = {"boy", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)
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
    opening: str
    landmark: str
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
class Gem:
    id: str
    label: str
    glow: str
    use: str
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
class Clue:
    id: str
    sign: str
    found_at: str
    points_to: str
    thinking: str
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
class HidingPlace:
    id: str
    label: str
    the: str
    habitat: str
    approach: str
    keeper: str
    surprise: str
    recovery_need: str
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
class Method:
    id: str
    label: str
    reaches: set[str]
    sense: int
    teamwork: str
    action: str
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"seeker", "partner"}]

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


def _r_loss_gloom(world: World) -> list[str]:
    gem = world.entities.get("gem")
    gate = world.entities.get("gate")
    if gem is None or gate is None:
        return []
    if gem.meters["lost"] < THRESHOLD:
        return []
    sig = ("loss_gloom", gem.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gate.meters["dim"] += 1
    for child in world.children():
        child.memes["worry"] += 1
    elder = world.entities.get("elder")
    if elder is not None:
        elder.memes["worry"] += 1
    return []


def _r_clue_hope(world: World) -> list[str]:
    if not world.facts.get("clue_found"):
        return []
    sig = ("clue_hope", world.facts.get("clue"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for child in world.children():
        child.memes["hope"] += 1
    return []


def _r_recovery_joy(world: World) -> list[str]:
    gem = world.entities.get("gem")
    gate = world.entities.get("gate")
    if gem is None or gate is None:
        return []
    if gem.meters["recovered"] < THRESHOLD:
        return []
    sig = ("recovery_joy", gem.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gate.meters["dim"] = 0.0
    for child in world.children():
        child.memes["joy"] += 1
        child.memes["pride"] += 1
    elder = world.entities.get("elder")
    if elder is not None:
        elder.memes["relief"] += 1
        elder.memes["gratitude"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="loss_gloom", tag="physical", apply=_r_loss_gloom),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_hope),
    Rule(name="recovery_joy", tag="emotional", apply=_r_recovery_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def clue_matches(clue: Clue, hiding: HidingPlace) -> bool:
    return clue.points_to == hiding.habitat


def method_fits(method: Method, hiding: HidingPlace) -> bool:
    return hiding.habitat in method.reaches and method.sense >= SENSE_MIN


def setting_affords(setting: Setting, hiding: HidingPlace) -> bool:
    return hiding.id in setting.affords


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for gem_id in GEMS:
            for clue_id, clue in CLUES.items():
                for hiding_id, hiding in HIDING_PLACES.items():
                    if not clue_matches(clue, hiding):
                        continue
                    if not setting_affords(setting, hiding):
                        continue
                    for method_id, method in METHODS.items():
                        if method_fits(method, hiding):
                            combos.append((setting_id, gem_id, clue_id, hiding_id, method_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    gem: str
    clue: str
    hiding: str
    method: str
    seeker_name: str
    seeker_gender: str
    partner_name: str
    partner_gender: str
    elder_type: str
    seeker_trait: str
    partner_trait: str
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


def introduce(world: World, seeker: Entity, partner: Entity, elder: Entity, gem_cfg: Gem) -> None:
    world.say(
        f"In an eastern village, {world.setting.opening} {world.setting.landmark}. "
        f"There {seeker.id} and {partner.id} often helped their {elder.label_word}, Elder Lin."
    )
    world.say(
        f"Above the gate hung the {gem_cfg.label}, a gem that {gem_cfg.use}. "
        f"Each evening it {gem_cfg.glow}, and the whole lane seemed to smile."
    )


def morning_loss(world: World, elder: Entity, gem_cfg: Gem) -> None:
    gem = world.get("gem")
    gem.meters["lost"] += 1
    world.facts["mystery_started"] = True
    propagate(world, narrate=False)
    world.say(
        f"One morning, just before the market drums, Elder Lin looked up and gave a soft cry. "
        f'The {gem_cfg.label} was gone from its little hook.'
    )
    world.say(
        f'"Without it," {elder.pronoun()} said, "the gate will not shine tonight, and the children '
        f'on the road home will miss its light."'
    )


def promise_help(world: World, seeker: Entity, partner: Entity) -> None:
    seeker.memes["duty"] += 1
    partner.memes["duty"] += 1
    world.say(
        f'{seeker.id} and {partner.id} looked at one another and nodded. '
        f'"We will search together," they said.'
    )


def find_clue(world: World, seeker: Entity, partner: Entity, clue: Clue) -> None:
    world.facts["clue_found"] = True
    world.facts["clue"] = clue.id
    propagate(world, narrate=False)
    world.say(
        f"At the foot of the gate they found {clue.sign} {clue.found_at}. "
        f"That was the first small answer in the mystery."
    )
    world.say(
        f"{seeker.id}, who was {seeker.attrs['skill_text']}, bent close. "
        f'{partner.id}, who was {partner.attrs["skill_text"]}, held the morning basket so nothing would be lost.'
    )


def reason_together(world: World, seeker: Entity, partner: Entity, clue: Clue, hiding: HidingPlace) -> None:
    seeker.memes["trust"] += 1
    partner.memes["trust"] += 1
    world.say(
        f'"Look," said {seeker.id}, "this means {clue.thinking}." '
        f'"Then we should search {hiding.the}," said {partner.id}.'
    )
    world.say(
        f"Neither child hurried ahead alone. They shared the guess, shared the path, and kept the mystery between them like a lantern with two handles."
    )


def travel(world: World, hiding: HidingPlace) -> None:
    world.say(
        f"So they went to {hiding.the}, {hiding.approach}."
    )


def recover(world: World, seeker: Entity, partner: Entity, hiding: HidingPlace, method: Method, gem_cfg: Gem) -> None:
    gem = world.get("gem")
    gem.meters["recovered"] += 1
    world.facts["recovered"] = True
    world.facts["surprise_keeper"] = hiding.keeper
    propagate(world, narrate=False)
    world.say(
        f"There they used {method.label}. {method.teamwork}"
    )
    world.say(
        f"Soon the children saw the {gem_cfg.label} glinting in the light. {hiding.surprise}"
    )
    world.say(
        f"{method.action}, and the gem came safely back into their hands."
    )


def restore(world: World, elder: Entity, seeker: Entity, partner: Entity, gem_cfg: Gem) -> None:
    gate = world.get("gate")
    gate.meters["lit"] += 1
    world.say(
        f"When they returned, Elder Lin set the {gem_cfg.label} back above the gate. "
        f"At sunset it {gem_cfg.glow} once more, brighter than before."
    )
    world.say(
        f"Travelers on the road smiled when they saw it, and {seeker.id} and {partner.id} stood a little taller."
    )
    elder.attrs["reward_ready"] = True


def reward_surprise(world: World, elder: Entity, seeker: Entity, partner: Entity) -> None:
    seeker.memes["surprise"] += 1
    partner.memes["surprise"] += 1
    elder.memes["kindness"] += 1
    world.say(
        f"Then came the surprise. Elder Lin opened a small red box and gave each child a tiny brass bell on a silk cord."
    )
    world.say(
        f'"These are for the two keepers of the gate," {elder.pronoun()} said. '
        f'When the bells chimed, they sounded like thanks itself.'
    )


def tell(
    setting: Setting,
    gem_cfg: Gem,
    clue: Clue,
    hiding: HidingPlace,
    method: Method,
    seeker_name: str = "Mei",
    seeker_gender: str = "girl",
    partner_name: str = "Jun",
    partner_gender: str = "boy",
    elder_type: str = "grandmother",
    seeker_trait: str = "keen-eyed",
    partner_trait: str = "steady-handed",
) -> World:
    world = World(setting)

    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_gender,
        role="seeker",
        traits=[seeker_trait],
        attrs={"skill_text": TRAIT_TEXT[seeker_trait]},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=[partner_trait],
        attrs={"skill_text": TRAIT_TEXT[partner_trait]},
    ))
    elder = world.add(Entity(
        id="Elder Lin",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
        attrs={"reward_ready": False},
    ))
    world.add(Entity(id="gate", type="gate", label="the village gate"))
    world.add(Entity(id="gem", type="gem", label=gem_cfg.label))
    world.facts.update(
        clue_found=False,
        clue=clue.id,
        recovered=False,
        mystery_started=False,
        surprise_keeper=hiding.keeper,
    )

    introduce(world, seeker, partner, elder, gem_cfg)
    world.para()
    morning_loss(world, elder, gem_cfg)
    promise_help(world, seeker, partner)

    world.para()
    find_clue(world, seeker, partner, clue)
    reason_together(world, seeker, partner, clue, hiding)
    travel(world, hiding)

    world.para()
    recover(world, seeker, partner, hiding, method, gem_cfg)
    restore(world, elder, seeker, partner, gem_cfg)
    reward_surprise(world, elder, seeker, partner)

    world.facts.update(
        seeker=seeker,
        partner=partner,
        elder=elder,
        gem_cfg=gem_cfg,
        clue_cfg=clue,
        hiding_cfg=hiding,
        method_cfg=method,
        gate_lit=world.get("gate").meters["lit"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "harbor": Setting(
        id="harbor",
        place="the harbor village",
        opening="white sails nodded in the mist beyond the tiled roofs,",
        landmark="A stone gate watched the road to the sea",
        affords={"reed_bank", "shrine_eaves"},
        tags={"village", "water"},
    ),
    "hills": Setting(
        id="hills",
        place="the hill village",
        opening="tea terraces curved like green ribbons under the dawn,",
        landmark="A painted gate stood where the eastern road bent downhill",
        affords={"pine_nest", "shrine_eaves"},
        tags={"village", "tree"},
    ),
    "river": Setting(
        id="river",
        place="the river village",
        opening="the river ran clear beside low bridges and willow shade,",
        landmark="An old gate marked the eastern path into town",
        affords={"pine_nest", "reed_bank"},
        tags={"village", "water", "tree"},
    ),
}

GEMS = {
    "dawn": Gem(
        id="dawn",
        label="Dawn Gem",
        glow="shone with a warm peach light",
        use="guided late walkers safely home",
        tags={"gem", "light"},
    ),
    "moon": Gem(
        id="moon",
        label="Moon Gem",
        glow="glimmered like milk in a blue bowl",
        use="cast a calm silver light over the lane",
        tags={"gem", "light"},
    ),
    "amber": Gem(
        id="amber",
        label="Amber Gem",
        glow="burned softly like honey in the sun",
        use="made the evening gate look friendly and bright",
        tags={"gem", "light"},
    ),
}

CLUES = {
    "feather": Clue(
        id="feather",
        sign="a black-and-white feather",
        found_at="beside the empty hook",
        points_to="tree",
        thinking="something from the trees visited the gate",
        tags={"bird", "clue"},
    ),
    "wet_tracks": Clue(
        id="wet_tracks",
        sign="three wet little tracks",
        found_at="on the stone step",
        points_to="water",
        thinking="the missing thing may have gone toward the river grass",
        tags={"water", "clue"},
    ),
    "scarlet_thread": Clue(
        id="scarlet_thread",
        sign="a scarlet thread from a festival kite",
        found_at="caught on the gate latch",
        points_to="roof",
        thinking="the wind carried more than dust across the roofs",
        tags={"wind", "clue"},
    ),
}

HIDING_PLACES = {
    "pine_nest": HidingPlace(
        id="pine_nest",
        label="pine nest",
        the="the crooked pine nest above the lane",
        habitat="tree",
        approach="where the branches whispered above the road",
        keeper="a magpie chick",
        surprise="A magpie chick had tucked it there, proud of anything that glittered.",
        recovery_need="high",
        tags={"bird", "tree"},
    ),
    "reed_bank": HidingPlace(
        id="reed_bank",
        label="reed bank",
        the="the reed bank by the slow bend of the river",
        habitat="water",
        approach="where dragonflies skimmed and the mud kept quiet secrets",
        keeper="an otter pup",
        surprise="An otter pup had rolled it there while chasing its own bright reflection.",
        recovery_need="water_edge",
        tags={"water", "otter"},
    ),
    "shrine_eaves": HidingPlace(
        id="shrine_eaves",
        label="shrine eaves",
        the="the shrine eaves above the market path",
        habitat="roof",
        approach="where red paper ribbons fluttered in the wind",
        keeper="a wind-snared kite",
        surprise="A torn festival kite had trapped the gem in its tangled tail.",
        recovery_need="high",
        tags={"wind", "roof"},
    ),
}

METHODS = {
    "ladder": Method(
        id="ladder",
        label="a bamboo ladder",
        reaches={"tree", "roof"},
        sense=3,
        teamwork="One child held the ladder firm below while the other climbed slowly, step by step.",
        action="With careful hands they loosened the snag and lowered it down",
        qa_text="They used a bamboo ladder together, with one child steadying it while the other reached the hiding place",
        tags={"ladder"},
    ),
    "rake": Method(
        id="rake",
        label="a long bamboo rake",
        reaches={"water"},
        sense=3,
        teamwork="One child knelt at the bank and guided the rake while the other held the basket ready and watched the current.",
        action="Working together, they drew it through the reeds without letting it slip away",
        qa_text="They used a long bamboo rake together, guiding it from the bank and catching the gem before the current could carry it off",
        tags={"rake"},
    ),
    "pole": Method(
        id="pole",
        label="a fishing pole with a silk loop",
        reaches={"tree", "water"},
        sense=2,
        teamwork="One child aimed the silk loop while the other whispered where to lift and when to pull.",
        action="After two patient tries, they hooked the gem gently",
        qa_text="They used a fishing pole with a silk loop, with one child aiming and the other calling out careful directions",
        tags={"pole"},
    ),
    "stool": Method(
        id="stool",
        label="a little wooden stool",
        reaches={"roof"},
        sense=1,
        teamwork="One child climbed on the stool while the other stretched both hands upward.",
        action="They almost reached, but it was never a safe plan",
        qa_text="They tried a stool",
        tags={"stool"},
    ),
}

GIRL_NAMES = ["Mei", "Lian", "Yun", "Bao", "Hua", "Lan", "Xia", "Fen"]
BOY_NAMES = ["Jun", "Wei", "Bo", "Ren", "Tao", "Ming", "Shen", "Kai"]
TRAITS = ["keen-eyed", "steady-handed", "patient", "quick-thinking", "gentle", "brave"]
TRAIT_TEXT = {
    "keen-eyed": "the best at noticing little things",
    "steady-handed": "good at careful work",
    "patient": "willing to wait for the right moment",
    "quick-thinking": "quick to fit one clue beside another",
    "gentle": "always careful with living creatures",
    "brave": "not afraid of high places or muddy banks",
}

KNOWLEDGE = {
    "gem": [(
        "What is a gem?",
        "A gem is a hard, shining stone that people treasure because it is beautiful. In stories, a gem often also carries meaning, like light, luck, or memory.",
    )],
    "bird": [(
        "Why do magpies take shiny things?",
        "Magpies notice bright, glittering objects because they catch the eye. A bird may carry one away out of curiosity, not because it understands who owns it.",
    )],
    "otter": [(
        "What does an otter like to do?",
        "An otter likes to swim, roll, and play in the water. Because it is playful, it may bat at something shiny if it sees it near the riverbank.",
    )],
    "wind": [(
        "How can wind move light things?",
        "Wind can catch paper, thread, and cloth and lift them or drag them along. If a shiny object is caught with them, it may be pulled somewhere surprising.",
    )],
    "ladder": [(
        "Why do people steady a ladder for each other?",
        "A ladder is safer when one person holds it while another climbs. That is a simple kind of teamwork, because both jobs matter at the same time.",
    )],
    "rake": [(
        "What is a rake used for?",
        "A rake has long teeth for pulling leaves, grass, or reeds toward you. In a careful search, it can help reach something that is just beyond your hands.",
    )],
    "pole": [(
        "Why is a long pole useful?",
        "A long pole helps you reach something far away without stepping into danger. It works best when people move slowly and guide one another.",
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork means people share a job and help each other do what one person alone could not do easily. In many folktales, good teamwork begins with listening as well as acting.",
    )],
}
KNOWLEDGE_ORDER = ["gem", "bird", "otter", "wind", "ladder", "rake", "pole", "teamwork"]


CURATED = [
    StoryParams(
        setting="hills",
        gem="moon",
        clue="feather",
        hiding="pine_nest",
        method="ladder",
        seeker_name="Mei",
        seeker_gender="girl",
        partner_name="Jun",
        partner_gender="boy",
        elder_type="grandmother",
        seeker_trait="keen-eyed",
        partner_trait="steady-handed",
    ),
    StoryParams(
        setting="river",
        gem="dawn",
        clue="wet_tracks",
        hiding="reed_bank",
        method="rake",
        seeker_name="Lan",
        seeker_gender="girl",
        partner_name="Wei",
        partner_gender="boy",
        elder_type="grandfather",
        seeker_trait="patient",
        partner_trait="quick-thinking",
    ),
    StoryParams(
        setting="harbor",
        gem="amber",
        clue="scarlet_thread",
        hiding="shrine_eaves",
        method="ladder",
        seeker_name="Bao",
        seeker_gender="girl",
        partner_name="Tao",
        partner_gender="boy",
        elder_type="grandmother",
        seeker_trait="gentle",
        partner_trait="brave",
    ),
    StoryParams(
        setting="river",
        gem="moon",
        clue="feather",
        hiding="pine_nest",
        method="pole",
        seeker_name="Hua",
        seeker_gender="girl",
        partner_name="Ming",
        partner_gender="boy",
        elder_type="grandfather",
        seeker_trait="quick-thinking",
        partner_trait="patient",
    ),
]


def explain_rejection(setting: Setting, clue: Clue, hiding: HidingPlace, method: Method) -> str:
    if not setting_affords(setting, hiding):
        return (
            f"(No story: {hiding.the} does not fit this village setting, so the search would not feel grounded there.)"
        )
    if not clue_matches(clue, hiding):
        return (
            f"(No story: the clue points toward {clue.points_to}, but {hiding.the} is a {hiding.habitat} place. The mystery needs a clue that honestly leads to its answer.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it is too weak or unsafe for this search. Choose a steadier method like ladder, rake, or pole.)"
        )
    return (
        f"(No story: {method.label} cannot reach {hiding.the}, so the teamwork would not really solve the problem.)"
    )


ASP_RULES = r"""
clue_matches(C,H) :- clue(C), hiding(H), points_to(C,R), habitat(H,R).
usable(M,H) :- method(M), hiding(H), habitat(H,R), reaches(M,R), sense(M,S), sense_min(Min), S >= Min.
valid(S,G,C,H,M) :- setting(S), gem(G), clue(C), hiding(H), method(M),
                    affords(S,H), clue_matches(C,H), usable(M,H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, hid))
    for gid in GEMS:
        lines.append(asp.fact("gem", gid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, clue.points_to))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        lines.append(asp.fact("habitat", hid, hiding.habitat))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        for reach in sorted(method.reaches):
            lines.append(asp.fact("reaches", mid, reach))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    partner = f["partner"]
    gem_cfg = f["gem_cfg"]
    return [
        f'Write a folk tale for a 3-to-5-year-old that includes the words "eastern" and "gem", and features a missing treasure solved by teamwork.',
        f"Tell a gentle mystery story where {seeker.id} and {partner.id} help an elder find the missing {gem_cfg.label} before nightfall.",
        "Write a simple folktale with a clue, a shared search, a surprise explanation, and an ending image of light returning to the village.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    partner = f["partner"]
    elder = f["elder"]
    gem_cfg = f["gem_cfg"]
    clue = f["clue_cfg"]
    hiding = f["hiding_cfg"]
    method = f["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that the {gem_cfg.label} had disappeared from the village gate. Without it, the gate would not shine that evening, so the children had to find the answer before sunset.",
        ),
        (
            "Who worked together to solve the mystery?",
            f"{seeker.id} and {partner.id} solved it together. They did not race against each other; they shared clues, guesses, and work from the beginning.",
        ),
        (
            "What clue did the children find?",
            f"They found {clue.sign} {clue.found_at}. That clue mattered because it pointed them toward a {clue.points_to} place instead of making them search everywhere at random.",
        ),
        (
            "How did the children recover the gem?",
            f"{method.qa_text}. Their teamwork mattered because one child watched and guided while the other did the reaching, so the plan stayed careful and calm.",
        ),
        (
            "What was the surprise?",
            f"The surprise was that the gem had not been stolen by a wicked thief at all. It was with {hiding.keeper}, so the mystery ended with understanding instead of anger.",
        ),
        (
            "How did the story end?",
            f"Elder Lin placed the {gem_cfg.label} back above the gate, and its light returned at sunset. Then the children received tiny brass bells, which showed that their good teamwork had changed how the village saw them.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"gem", "teamwork"}
    clue = f["clue_cfg"]
    hiding = f["hiding_cfg"]
    method = f["method_cfg"]
    tags |= set(clue.tags)
    tags |= set(hiding.tags)
    tags |= set(method.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: an eastern village mystery about a missing gem, teamwork, and a surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gem", choices=GEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting is not None and args.setting not in SETTINGS:
        raise StoryError("(Unknown setting.)")
    if args.gem is not None and args.gem not in GEMS:
        raise StoryError("(Unknown gem.)")
    if args.clue is not None and args.clue not in CLUES:
        raise StoryError("(Unknown clue.)")
    if args.hiding is not None and args.hiding not in HIDING_PLACES:
        raise StoryError("(Unknown hiding place.)")
    if args.method is not None and args.method not in METHODS:
        raise StoryError("(Unknown method.)")

    if args.setting and args.clue and args.hiding and args.method:
        setting = SETTINGS[args.setting]
        clue = CLUES[args.clue]
        hiding = HIDING_PLACES[args.hiding]
        method = METHODS[args.method]
        if not (setting_affords(setting, hiding) and clue_matches(clue, hiding) and method_fits(method, hiding)):
            raise StoryError(explain_rejection(setting, clue, hiding, method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.gem is None or combo[1] == args.gem)
        and (args.clue is None or combo[2] == args.clue)
        and (args.hiding is None or combo[3] == args.hiding)
        and (args.method is None or combo[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, gem_id, clue_id, hiding_id, method_id = rng.choice(sorted(combos))
    seeker_name, seeker_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=seeker_name)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    seeker_trait, partner_trait = rng.sample(TRAITS, 2)

    return StoryParams(
        setting=setting_id,
        gem=gem_id,
        clue=clue_id,
        hiding=hiding_id,
        method=method_id,
        seeker_name=seeker_name,
        seeker_gender=seeker_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        elder_type=elder_type,
        seeker_trait=seeker_trait,
        partner_trait=partner_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.gem not in GEMS:
        raise StoryError(f"(Unknown gem '{params.gem}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue '{params.clue}'.)")
    if params.hiding not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place '{params.hiding}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}'.)")
    if params.seeker_trait not in TRAIT_TEXT:
        raise StoryError(f"(Unknown seeker trait '{params.seeker_trait}'.)")
    if params.partner_trait not in TRAIT_TEXT:
        raise StoryError(f"(Unknown partner trait '{params.partner_trait}'.)")
    if params.elder_type not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown elder type '{params.elder_type}'.)")

    setting = SETTINGS[params.setting]
    gem_cfg = GEMS[params.gem]
    clue = CLUES[params.clue]
    hiding = HIDING_PLACES[params.hiding]
    method = METHODS[params.method]
    if not (setting_affords(setting, hiding) and clue_matches(clue, hiding) and method_fits(method, hiding)):
        raise StoryError(explain_rejection(setting, clue, hiding, method))

    world = tell(
        setting=setting,
        gem_cfg=gem_cfg,
        clue=clue,
        hiding=hiding,
        method=method,
        seeker_name=params.seeker_name,
        seeker_gender=params.seeker_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        elder_type=params.elder_type,
        seeker_trait=params.seeker_trait,
        partner_trait=params.partner_trait,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = [CURATED[0]]
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(17)))
    except StoryError:
        rc = 1
        print("MISMATCH: default resolve_params() failed during smoke test setup.")
        smoke_cases = [CURATED[0]]

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=True, qa=True, header=f"smoke {i}")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on case {i}: {err}")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, gem, clue, hiding, method) combos:\n")
        for setting, gem, clue, hiding, method in combos:
            print(f"  {setting:7} {gem:6} {clue:14} {hiding:12} {method}")
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
                f"### {p.seeker_name} & {p.partner_name}: {p.gem} / {p.clue} / "
                f"{p.hiding} / {p.method}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
