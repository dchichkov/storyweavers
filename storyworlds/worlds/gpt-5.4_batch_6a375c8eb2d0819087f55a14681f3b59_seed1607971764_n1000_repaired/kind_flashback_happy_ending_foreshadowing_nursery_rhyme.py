#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kind_flashback_happy_ending_foreshadowing_nursery_rhyme.py
=====================================================================================

A standalone storyworld for a gentle nursery-rhyme-like tale about a kind child
who notices a small creature in trouble, remembers an earlier kindness, and
helps the creature home before the hinted rain comes down.

The world is built around three story instruments requested by the seed:
- Foreshadowing: the opening notices signs of rain and signs that some little
  creature is out of place.
- Flashback: the helper remembers a past moment when an older loved one was kind.
- Happy ending: the creature gets home safely, the weather clears, and the day
  ends in a bright image.

The world model prefers only physically and socially plausible rescues:
a basket can carry some creatures, a shawl can wrap only small soft ones, a
ribbon can gently lead a lamb, and so on. Invalid combinations are rejected with
a plain explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/kind_flashback_happy_ending_foreshadowing_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/kind_flashback_happy_ending_foreshadowing_nursery_rhyme.py --creature lamb --aid ribbon
    python storyworlds/worlds/gpt-5.4/kind_flashback_happy_ending_foreshadowing_nursery_rhyme.py --creature hedgehog --aid shawl
    python storyworlds/worlds/gpt-5.4/kind_flashback_happy_ending_foreshadowing_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/kind_flashback_happy_ending_foreshadowing_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/kind_flashback_happy_ending_foreshadowing_nursery_rhyme.py --verify
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
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mother",
            "father": "father",
            "aunt": "aunt",
            "uncle": "uncle",
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
class Setting:
    id: str
    place: str
    sign: str
    path: str
    creatures: set[str] = field(default_factory=set)
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
    article: str
    sound: str
    home: str
    keeper: str
    home_path: str
    small: bool = True
    prickly: bool = False
    walks: bool = False
    water_friendly: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
class Aid:
    id: str
    label: str
    phrase: str
    action: str
    carries: set[str] = field(default_factory=set)
    leads: set[str] = field(default_factory=set)
    warms: bool = False
    shelters: bool = False
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
class Memory:
    id: str
    elder_type: str
    line1: str
    line2: str
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


def _r_lost_creature(world: World) -> list[str]:
    creature = world.get("creature")
    hero = world.get("hero")
    if creature.meters["lost"] < THRESHOLD:
        return []
    sig = ("lost", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.memes["fear"] += 1
    hero.memes["concern"] += 1
    return []


def _r_drizzle_chill(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["lost"] < THRESHOLD:
        return []
    if world.get("sky").meters["drizzle"] < THRESHOLD:
        return []
    if world.facts.get("sheltered", False):
        return []
    sig = ("chill", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["cold"] += 1
    creature.memes["fear"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="lost_creature", tag="emotional", apply=_r_lost_creature),
    Rule(name="drizzle_chill", tag="physical", apply=_r_drizzle_chill),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def aid_can_help(aid: Aid, creature: CreatureCfg) -> bool:
    return creature.id in aid.carries or creature.id in aid.leads


def place_supports(setting: Setting, creature: CreatureCfg) -> bool:
    return creature.id in setting.creatures


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for creature_id, creature in CREATURES.items():
            if not place_supports(setting, creature):
                continue
            for aid_id, aid in AIDS.items():
                if aid_can_help(aid, creature):
                    out.append((setting_id, creature_id, aid_id))
    return out


def rescue_style(aid: Aid, creature: CreatureCfg) -> str:
    if creature.id in aid.carries:
        return "carry"
    if creature.id in aid.leads:
        return "lead"
    return "none"


def outcome_of(params: "StoryParams") -> str:
    if params.setting not in SETTINGS or params.creature not in CREATURES or params.aid not in AIDS:
        raise StoryError("(No story: one of the chosen ids is not in this world.)")
    creature = CREATURES[params.creature]
    aid = AIDS[params.aid]
    if not place_supports(SETTINGS[params.setting], creature):
        raise StoryError(explain_rejection(SETTINGS[params.setting], creature, aid))
    if not aid_can_help(aid, creature):
        raise StoryError(explain_rejection(SETTINGS[params.setting], creature, aid))
    if params.delay == 0:
        return "cozy"
    return "cozy" if (aid.warms or aid.shelters) else "damp"


def explain_rejection(setting: Setting, creature: CreatureCfg, aid: Aid) -> str:
    if not place_supports(setting, creature):
        return (
            f"(No story: {creature.label} does not belong in {setting.place} here, "
            f"so the opening clue would feel ungrounded. Pick a creature that fits this place.)"
        )
    if not aid_can_help(aid, creature):
        if creature.prickly and aid.id == "shawl":
            return (
                f"(No story: a shawl is too soft for a prickly {creature.label}. "
                f"This world uses a basket for that kind rescue.)"
            )
        if creature.walks and aid.id in {"basket", "shawl"}:
            return (
                f"(No story: {creature.label.capitalize()} is better guided gently home than bundled up. "
                f"Try an aid that can lead it.)"
            )
        return (
            f"(No story: {aid.label} does not sensibly help a {creature.label} in this world. "
            f"Pick an aid that can carry or gently lead the creature home.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_comfort(world: World, aid: Aid) -> dict:
    sim = world.copy()
    if sim.facts["delay"] > 0:
        sim.get("sky").meters["drizzle"] += 1
        propagate(sim, narrate=False)
    if aid.warms or aid.shelters:
        sim.facts["sheltered"] = True
        if sim.get("creature").meters["cold"] >= THRESHOLD:
            sim.get("creature").meters["cold"] = 0.0
    return {
        "cold": sim.get("creature").meters["cold"],
        "fear": sim.get("creature").memes["fear"],
    }


def opening_rhyme(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"{hero.id} skipped by {setting.place}, light of shoe and light of chin. "
        f"{hero.pronoun().capitalize()} hummed a little market tune, with morning tucked within."
    )
    world.say(
        f"But {setting.sign}, and on {setting.path} there lay a clue so small and thin. "
        f"It seemed to say, before long that day, some tiny trouble would begin."
    )


def see_creature(world: World, hero: Entity, creature: Entity, cfg: CreatureCfg) -> None:
    creature.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came a {cfg.sound} by the path, a soft and shaky little cry. "
        f"There stood {cfg.article} {cfg.label}, away from {cfg.home}, with worried, wondering eye."
    )
    if creature.memes["fear"] >= THRESHOLD:
        world.say(
            f"{cfg.article.capitalize()} {cfg.label} looked small and scared, "
            f"as if the world had grown too wide."
        )


def flashback(world: World, hero: Entity, elder: Entity, memory: Memory) -> None:
    hero.memes["kindness"] += 1
    hero.memes["remembering"] += 1
    world.say(
        f"At once {hero.id} remembered then a yester-morn, a softer sky: "
        f"{memory.line1}"
    )
    world.say(
        f"{memory.line2} So back into {hero.pronoun('possessive')} heart there came "
        f"a kind and steady try."
    )


def decide_help(world: World, hero: Entity, creature: Entity, aid: Aid, cfg: CreatureCfg) -> None:
    pred = predict_comfort(world, aid)
    world.facts["predicted_cold"] = pred["cold"]
    if pred["cold"] >= THRESHOLD:
        danger = "The drizzle would make the poor thing colder if nobody hurried."
    else:
        danger = "A quick, gentle help would keep the poor thing snug and safe."
    world.say(
        f'{hero.id} looked at {aid.phrase} and whispered, "A kind hand first, a song hand later." '
        f"{danger}"
    )
    if rescue_style(aid, cfg) == "carry":
        world.say(
            f"{hero.pronoun().capitalize()} used {aid.phrase} and moved as slow as a nursery rhyme."
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} reached with patient fingers, gentle as a bell chime."
        )


def drizzle(world: World) -> None:
    world.get("sky").meters["drizzle"] += 1
    propagate(world, narrate=False)
    if world.get("creature").meters["cold"] >= THRESHOLD:
        world.say(
            "Soon little drops began to tap, drip-drop upon the lane. "
            "The small one shivered where it stood beneath the silver rain."
        )
    else:
        world.say(
            "Soon little drops began to tap, but help was close at hand. "
            "The sky sang low above them both, a light and misty band."
        )


def rescue(world: World, hero: Entity, creature: Entity, cfg: CreatureCfg, aid: Aid) -> None:
    style = rescue_style(aid, cfg)
    if style == "carry":
        world.facts["sheltered"] = bool(aid.warms or aid.shelters)
        if aid.warms:
            creature.meters["cold"] = 0.0
        creature.meters["carried"] += 1
        world.say(
            f"{hero.id} {aid.action} the {cfg.label}, snug and still, and turned toward {cfg.home_path}."
        )
    else:
        creature.meters["led"] += 1
        world.say(
            f"{hero.id} {aid.action} and guided the {cfg.label} toward {cfg.home_path}, step by careful step."
        )
    creature.meters["lost"] = 0.0
    creature.memes["fear"] = 0.0
    creature.memes["trust"] += 1
    hero.memes["joy"] += 1
    hero.memes["kindness"] += 1


def reunion(world: World, hero: Entity, creature: Entity, cfg: CreatureCfg, elder: Entity) -> None:
    creature.meters["home"] += 1
    world.say(
        f"By {cfg.home} there came a call -- {cfg.keeper} at last in sight. "
        f"The little one gave a brighter cry and hurried toward the light."
    )
    world.say(
        f'"Thank you for being kind," said {elder.label_word}, smiling at {hero.id}. '
        f'"A small heart remembers shelter long, and so does mine tonight."'
    )


def ending(world: World, hero: Entity, cfg: CreatureCfg, outcome: str) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    if outcome == "cozy":
        world.say(
            f"Then out peeped sun through thinning cloud; gold laid lace on leaf and line. "
            f"{hero.id} went on with a lighter step, and the day felt warm and fine."
        )
    else:
        world.say(
            f"The drops still danced on fence and stone, yet all was safe and bright. "
            f"{hero.id} laughed and shook the rain, with a happy heart alight."
        )
    world.say(
        f"And if you ask what made things right, not silver shoe nor weather kind -- "
        f"it was one small pause, one kindly thought, and one brave, gentle mind."
    )
def tell(
    creature_cfg: Creature,
    aid: Aid,
    memory: Memory,
    hero_name: str,
    hero_type: HeroType,
    trait: Trait,
    delay: Delay,
    setting=None,
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=memory.elder_type,
        label="the elder",
        role="elder",
        attrs={},
    ))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type=creature_cfg.id,
        label=creature_cfg.label,
        role="creature",
        attrs={"home": creature_cfg.home, "keeper": creature_cfg.keeper},
    ))
    sky = world.add(Entity(
        id="sky",
        kind="thing",
        type="weather",
        label="the sky",
        role="weather",
        attrs={},
    ))
    tool = world.add(Entity(
        id="aid",
        kind="thing",
        type="aid",
        label=aid.label,
        role="aid",
        attrs={},
    ))

    world.facts["sheltered"] = False
    world.facts["delay"] = delay
    world.facts["foreshadow_sign"] = setting.sign
    world.facts["memory"] = memory
    world.facts["helper_style"] = rescue_style(aid, creature_cfg)
    world.facts["predicted_cold"] = 0.0

    opening_rhyme(world, hero, setting)

    world.para()
    see_creature(world, hero, creature, creature_cfg)
    flashback(world, hero, elder, memory)
    decide_help(world, hero, creature, aid, creature_cfg)

    world.para()
    if delay > 0:
        drizzle(world)
    rescue(world, hero, creature, creature_cfg, aid)
    reunion(world, hero, creature, creature_cfg, elder)

    world.para()
    world_outcome = outcome_of(StoryParams(
        setting=setting.id,
        creature=creature_cfg.id,
        aid=aid.id,
        memory=memory.id,
        name=hero_name,
        gender=hero_type,
        trait=trait,
        delay=delay,
        seed=None,
    ))
    ending(world, hero, creature_cfg, world_outcome)

    world.facts.update(
        hero=hero,
        elder=elder,
        creature=creature,
        creature_cfg=creature_cfg,
        aid=aid,
        setting=setting,
        outcome=world_outcome,
        memory_cfg=memory,
        rescued=True,
        got_cold=creature.meters["cold"] >= THRESHOLD,
        reached_home=creature.meters["home"] >= THRESHOLD,
    )
    return world
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


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden gate",
        sign="a gray cloud curled over the bean-pole row",
        path="the damp brick path",
        creatures={"kitten", "hedgehog", "lamb"},
        tags={"garden", "rain"},
    ),
    "lane": Setting(
        id="lane",
        place="the cobbled lane",
        sign="the wind teased straw in a twirling ring",
        path="the puddled stones",
        creatures={"kitten", "lamb"},
        tags={"lane", "rain"},
    ),
    "pond": Setting(
        id="pond",
        place="the pond-side walk",
        sign="the reeds bent low and the swallows skimmed near",
        path="the mossy edge",
        creatures={"duckling", "hedgehog"},
        tags={"pond", "rain"},
    ),
}

CREATURES = {
    "kitten": CreatureCfg(
        id="kitten",
        label="kitten",
        article="a",
        sound="mew-mew",
        home="the bakery porch",
        keeper="mother cat",
        home_path="the porch with the blue milk bowl",
        small=True,
        prickly=False,
        walks=False,
        water_friendly=False,
        tags={"kitten", "animal"},
    ),
    "duckling": CreatureCfg(
        id="duckling",
        label="duckling",
        article="a",
        sound="peep-peep",
        home="the reed nest",
        keeper="mother duck",
        home_path="the reeds beside the pond",
        small=True,
        prickly=False,
        walks=False,
        water_friendly=True,
        tags={"duckling", "animal", "pond"},
    ),
    "hedgehog": CreatureCfg(
        id="hedgehog",
        label="hedgehog",
        article="a",
        sound="sniff-sniff",
        home="the leafy hedge nook",
        keeper="hedgehog mother",
        home_path="the hedge with brown leaves under it",
        small=True,
        prickly=True,
        walks=False,
        water_friendly=False,
        tags={"hedgehog", "animal"},
    ),
    "lamb": CreatureCfg(
        id="lamb",
        label="lamb",
        article="a",
        sound="baa-baa",
        home="the red barn",
        keeper="the ewe",
        home_path="the barn with the red door",
        small=False,
        prickly=False,
        walks=True,
        water_friendly=False,
        tags={"lamb", "animal", "farm"},
    ),
}

AIDS = {
    "basket": Aid(
        id="basket",
        label="basket",
        phrase="a willow basket",
        action="lifted the little traveler into the willow basket",
        carries={"kitten", "duckling", "hedgehog"},
        leads=set(),
        warms=True,
        shelters=True,
        tags={"basket", "carry"},
    ),
    "shawl": Aid(
        id="shawl",
        label="shawl",
        phrase="a warm wool shawl",
        action="wrapped the small one in the warm wool shawl",
        carries={"kitten", "duckling"},
        leads=set(),
        warms=True,
        shelters=True,
        tags={"shawl", "warmth"},
    ),
    "ribbon": Aid(
        id="ribbon",
        label="ribbon",
        phrase="a soft blue ribbon",
        action="looped the soft blue ribbon loosely and kindly",
        carries=set(),
        leads={"lamb"},
        warms=False,
        shelters=False,
        tags={"ribbon", "lead"},
    ),
    "wagon": Aid(
        id="wagon",
        label="wagon",
        phrase="a little red wagon",
        action="settled the traveler in the little red wagon",
        carries={"kitten", "duckling", "lamb"},
        leads=set(),
        warms=False,
        shelters=False,
        tags={"wagon", "carry"},
    ),
}

MEMORIES = {
    "grandma_shawl": Memory(
        id="grandma_shawl",
        elder_type="grandmother",
        line1="Grandma had once found her shivering after a splashy fall and tucked a shawl around her shoulders.",
        line2='She had said, "When you can, be kind first; the world grows warmer that way."',
        tags={"grandma", "kindness"},
    ),
    "grandpa_wait": Memory(
        id="grandpa_wait",
        elder_type="grandfather",
        line1="Grandpa had once waited with her at a windy corner when she had dropped her satchel and nearly cried.",
        line2='He had said, "A patient minute can turn a hard one sweet."',
        tags={"grandpa", "kindness"},
    ),
    "aunt_hand": Memory(
        id="aunt_hand",
        elder_type="aunt",
        line1="Aunt May had once held her hand all the way home when thunder had sounded too big for small ears.",
        line2='She had said, "Kind feet slow down for frightened feet."',
        tags={"aunt", "kindness"},
    ),
}

GIRL_NAMES = ["Molly", "Daisy", "Lila", "Nell", "Rosie", "Mabel", "Tilly", "June"]
BOY_NAMES = ["Toby", "Finn", "Ollie", "Ned", "Milo", "Bram", "Jory", "Pip"]
TRAITS = ["gentle", "bright", "patient", "merry", "tender", "careful"]


KNOWLEDGE = {
    "rain": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives a little hint early about something that will matter later. A dark cloud or a worried sound can gently tell you trouble is coming."
        ),
        (
            "Why do animals need shelter from cold rain?",
            "Cold rain can make a small animal lose warmth and feel unsafe. Shelter helps its body stay warmer and calmer."
        ),
    ],
    "flashback": [
        (
            "What is a flashback?",
            "A flashback is when a story pauses the present moment to remember something from before. That older memory can help explain why a character makes a choice now."
        ),
    ],
    "kindness": [
        (
            "What does it mean to be kind?",
            "Being kind means noticing what someone needs and trying to help in a gentle way. Kindness often uses both careful hands and thoughtful words."
        ),
    ],
    "basket": [
        (
            "Why is a basket useful for carrying a tiny animal?",
            "A basket can hold a small animal safely while someone walks slowly. Its sides help keep the animal from slipping away."
        ),
    ],
    "shawl": [
        (
            "What does a warm shawl do?",
            "A shawl wraps around a body and helps keep warmth in. That can comfort someone who feels chilly or scared."
        ),
    ],
    "ribbon": [
        (
            "Why should a ribbon be used gently with an animal?",
            "A ribbon should be loose and gentle so it guides without hurting. Kind help never yanks or scares."
        ),
    ],
    "wagon": [
        (
            "What is a wagon good for?",
            "A wagon can carry something while wheels do the heavy work. It helps move a load without making small legs do all the walking."
        ),
    ],
    "kitten": [
        (
            "What sound does a kitten make?",
            "A kitten often mews or meows in a small voice. That sound can tell you it wants comfort or help."
        ),
    ],
    "duckling": [
        (
            "Where do ducklings like to stay safe?",
            "Ducklings stay safest close to their mother and near the place she leads them. Being separated can make them confused even if they like water."
        ),
    ],
    "hedgehog": [
        (
            "Why would a hedgehog need a basket instead of a soft shawl?",
            "A hedgehog has prickles that can catch in soft cloth. A basket is firmer and safer for carrying one."
        ),
    ],
    "lamb": [
        (
            "Why is a lamb often guided instead of wrapped up and carried?",
            "A lamb can usually walk on its own if someone leads it gently. Guiding respects its size and keeps the rescue calm."
        ),
    ],
}
KNOWLEDGE_ORDER = [
    "flashback",
    "rain",
    "kindness",
    "basket",
    "shawl",
    "ribbon",
    "wagon",
    "kitten",
    "duckling",
    "hedgehog",
    "lamb",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    creature = f["creature_cfg"]
    setting = f["setting"]
    memory = f["memory_cfg"]
    return [
        f'Write a short nursery-rhyme-style story that uses the word "kind" and takes place by {setting.place}.',
        f"Tell a gentle story where {hero.id} hears {creature.sound}, remembers a past kindness from {memory.elder_type}, and helps a {creature.label} home before the rain.",
        'Write a child-facing story with foreshadowing, a flashback, and a happy ending, showing that a kind pause can change the whole day.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    creature = f["creature_cfg"]
    setting = f["setting"]
    aid = f["aid"]
    elder = f["elder"]
    outcome = f["outcome"]
    helper_style = f["helper_style"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child walking by {setting.place}, and a little {creature.label} that needed help. The story also remembers {elder.label_word}, whose earlier kindness shaped what {hero.id} did."
        ),
        (
            "What hinted early that something was about to happen?",
            f"The story begins with {f['foreshadow_sign']} and a tiny clue on {setting.path}. Those details foreshadow that a small problem is coming before the child even hears the cry."
        ),
        (
            f"Why did {hero.id} stop to help the {creature.label}?",
            f"{hero.id} heard the frightened {creature.sound} and saw that the little one was away from {creature.home}. {hero.pronoun('subject').capitalize()} also remembered how {elder.label_word} had once been kind, so that memory turned concern into action."
        ),
        (
            "How is the flashback important in this story?",
            f"The flashback shows an older moment when {elder.label_word} helped {hero.id} during a hard time. Because of that remembered kindness, {hero.id} chooses to be kind in the present instead of hurrying on."
        ),
    ]
    if helper_style == "carry":
        qa.append(
            (
                f"How did {hero.id} help the {creature.label}?",
                f"{hero.id} used {aid.phrase} to carry the little one toward {creature.home_path}. That method matched the creature's size and kept the rescue gentle."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} help the {creature.label}?",
                f"{hero.id} used {aid.phrase} to guide the {creature.label} step by step toward {creature.home_path}. That was kinder than trying to bundle up an animal meant to walk."
            )
        )
    if outcome == "cozy":
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the {creature.label} back home and the day feeling warm again. The ending image proves that the kind rescue changed fear into safety and joy."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It still ended happily, even though the rain stayed on fence and stone. The {creature.label} was safe at home, and that mattered more than the wet weather."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"flashback", "rain", "kindness"}
    tags |= set(f["aid"].tags)
    tags |= set(f["creature_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} helper_style={world.facts.get('helper_style')} sheltered={world.facts.get('sheltered')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    setting: str
    creature: str
    aid: str
    memory: str
    name: str
    gender: str
    trait: str
    delay: int = 1
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        setting="garden",
        creature="kitten",
        aid="shawl",
        memory="grandma_shawl",
        name="Molly",
        gender="girl",
        trait="gentle",
        delay=1,
        seed=None,
    ),
    StoryParams(
        setting="pond",
        creature="duckling",
        aid="basket",
        memory="aunt_hand",
        name="Toby",
        gender="boy",
        trait="careful",
        delay=0,
        seed=None,
    ),
    StoryParams(
        setting="garden",
        creature="hedgehog",
        aid="basket",
        memory="grandpa_wait",
        name="Lila",
        gender="girl",
        trait="patient",
        delay=1,
        seed=None,
    ),
    StoryParams(
        setting="lane",
        creature="lamb",
        aid="ribbon",
        memory="aunt_hand",
        name="Finn",
        gender="boy",
        trait="tender",
        delay=1,
        seed=None,
    ),
    StoryParams(
        setting="lane",
        creature="kitten",
        aid="wagon",
        memory="grandma_shawl",
        name="Nell",
        gender="girl",
        trait="bright",
        delay=0,
        seed=None,
    ),
]


ASP_RULES = r"""
% a setting supports a creature if that creature belongs there
supports(S, C) :- setting(S), creature(C), found_in(S, C).

% an aid helps if it can carry or lead the creature
helps(A, C) :- carries(A, C).
helps(A, C) :- leads(A, C).

valid(S, C, A) :- supports(S, C), helps(A, C).

% outcome model: all valid stories end happily, but the texture differs
% if rain comes before rescue and the aid does not warm or shelter.
cozy :- chosen_delay(0).
cozy :- chosen_delay(D), D > 0, chosen_aid(A), warms(A).
cozy :- chosen_delay(D), D > 0, chosen_aid(A), shelters(A).
outcome(cozy) :- cozy.
outcome(damp) :- not cozy.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for creature_id in sorted(setting.creatures):
            lines.append(asp.fact("found_in", setting_id, creature_id))
    for creature_id in CREATURES:
        lines.append(asp.fact("creature", creature_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for creature_id in sorted(aid.carries):
            lines.append(asp.fact("carries", aid_id, creature_id))
        for creature_id in sorted(aid.leads):
            lines.append(asp.fact("leads", aid_id, creature_id))
        if aid.warms:
            lines.append(asp.fact("warms", aid_id))
        if aid.shelters:
            lines.append(asp.fact("shelters", aid_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_aid", params.aid),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        py_outcome = outcome_of(params)
        asp_res = asp_outcome(params)
        if py_outcome != asp_res:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches ASP on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        smoke_params.seed = 7
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Verify failed: generated empty story.)")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a kind child, a remembered kindness, a small rescue in nursery-rhyme style."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = help reaches the creature before the drizzle; 1 = the drizzle starts first")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, creature, aid) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.creature and args.aid:
        setting = SETTINGS[args.setting]
        creature = CREATURES[args.creature]
        aid = AIDS[args.aid]
        if not (place_supports(setting, creature) and aid_can_help(aid, creature)):
            raise StoryError(explain_rejection(setting, creature, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.creature is None or combo[1] == args.creature)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, creature_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    memory = args.memory or rng.choice(sorted(MEMORIES))
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    return StoryParams(
        setting=setting_id,
        creature=creature_id,
        aid=aid_id,
        memory=memory,
        name=name,
        gender=gender,
        trait=trait,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.creature not in CREATURES:
        raise StoryError(f"(No story: unknown creature '{params.creature}'.)")
    if params.aid not in AIDS:
        raise StoryError(f"(No story: unknown aid '{params.aid}'.)")
    if params.memory not in MEMORIES:
        raise StoryError(f"(No story: unknown memory '{params.memory}'.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown gender '{params.gender}'.)")
    if params.delay not in {0, 1}:
        raise StoryError("(No story: delay must be 0 or 1.)")

    setting = SETTINGS[params.setting]
    creature = CREATURES[params.creature]
    aid = AIDS[params.aid]
    if not (place_supports(setting, creature) and aid_can_help(aid, creature)):
        raise StoryError(explain_rejection(setting, creature, aid))

    world = tell(
        setting=setting,
        creature_cfg=creature,
        aid=aid,
        memory=MEMORIES[params.memory],
        hero_name=params.name,
        hero_type=params.gender,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (setting, creature, aid) combos:\n")
        for setting_id, creature_id, aid_id in combos:
            print(f"  {setting_id:8} {creature_id:10} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.creature} at {p.setting} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
