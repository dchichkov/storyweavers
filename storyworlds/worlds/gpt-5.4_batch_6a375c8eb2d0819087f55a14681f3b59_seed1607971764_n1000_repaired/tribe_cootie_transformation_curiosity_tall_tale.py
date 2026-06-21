#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tribe_cootie_transformation_curiosity_tall_tale.py
=============================================================================

A standalone story world for a tall-tale-flavored story about a child from a
tribe who becomes wildly curious about a strange "cootie" cocoon and learns
that gentle care can lead to a marvelous transformation.

The core premise:
- A child in a tribe finds an odd cocoon or chrysalis.
- Someone jokes that it is a "cootie," which makes the child even more curious.
- The child wants to know what is inside.
- A wise grown-up suggests a gentle way to watch and care for it instead of
  poking or prying.
- If the child protects the cocoon in the right shelter long enough, it
  transforms into a wondrous creature.
- If the child is too rough, the cocoon is damaged and the transformation fails.

The world model carries both physical meters and emotional memes. Prose is
rendered from simulated state, not from one frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/tribe_cootie_transformation_curiosity_tall_tale.py
    python storyworlds/worlds/gpt-5.4/tribe_cootie_transformation_curiosity_tall_tale.py --tribe river_reed --cocoon moon_moth
    python storyworlds/worlds/gpt-5.4/tribe_cootie_transformation_curiosity_tall_tale.py --care pry_open
    python storyworlds/worlds/gpt-5.4/tribe_cootie_transformation_curiosity_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/tribe_cootie_transformation_curiosity_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tribe_cootie_transformation_curiosity_tall_tale.py --verify
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
PATIENCE_GOAL = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle"}
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
            "mother": "mother",
            "father": "father",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
class Tribe:
    id: str
    label: str
    place: str
    boast: str
    camp_image: str
    watcher_spot: str
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
class CocoonKind:
    id: str
    label: str
    phrase: str
    casing: str
    hatch_noun: str
    transformed_label: str
    transformed_phrase: str
    habitat: str
    needs: set[str]
    glow: str
    opening: str
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
class Shelter:
    id: str
    label: str
    phrase: str
    provides: set[str]
    image: str
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
class CareMethod:
    id: str
    label: str
    gentle: bool
    supports: set[str]
    damages: bool
    opening_line: str
    try_line: str
    help_line: str
    qa_line: str
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
class Elder:
    id: str
    type: str
    title: str
    advice: str
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


def _r_damage_stops_change(world: World) -> list[str]:
    cocoon = world.get("cocoon")
    if cocoon.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_stops_change", "cocoon")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cocoon.meters["ready"] = 0.0
    cocoon.meters["transformed"] = 0.0
    cocoon.memes["startled"] += 1
    return []


def _r_ready(world: World) -> list[str]:
    cocoon = world.get("cocoon")
    if cocoon.meters["damaged"] >= THRESHOLD:
        return []
    if cocoon.meters["sheltered"] < THRESHOLD:
        return []
    if cocoon.meters["gentle_touch"] < THRESHOLD:
        return []
    if cocoon.meters["patience"] < PATIENCE_GOAL:
        return []
    sig = ("ready", "cocoon")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cocoon.meters["ready"] += 1
    return ["__ready__"]


def _r_transform(world: World) -> list[str]:
    cocoon = world.get("cocoon")
    if cocoon.meters["ready"] < THRESHOLD:
        return []
    sig = ("transform", "cocoon")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cocoon.meters["transformed"] += 1
    hero = world.get("hero")
    elder = world.get("elder")
    hero.memes["wonder"] += 1
    hero.memes["fear"] = 0.0
    elder.memes["pride"] += 1
    return ["__transformed__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_stops_change", tag="physical", apply=_r_damage_stops_change),
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="transform", tag="physical", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            if sent.startswith("__"):
                continue
            world.say(sent)
    return produced


def shelter_works(cocoon: CocoonKind, shelter: Shelter) -> bool:
    return cocoon.needs.issubset(shelter.provides)


def care_is_reasonable(care: CareMethod) -> bool:
    return care.gentle and not care.damages


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for tribe_id in TRIBES:
        for cocoon_id, cocoon in COCOONS.items():
            for shelter_id, shelter in SHELTERS.items():
                if shelter_works(cocoon, shelter):
                    combos.append((tribe_id, cocoon_id, shelter_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.care not in CARE_METHODS:
        return "invalid"
    if params.cocoon not in COCOONS or params.shelter not in SHELTERS:
        return "invalid"
    cocoon = COCOONS[params.cocoon]
    shelter = SHELTERS[params.shelter]
    care = CARE_METHODS[params.care]
    if not shelter_works(cocoon, shelter):
        return "invalid"
    if care.damages:
        return "spoiled"
    if not care.gentle:
        return "spoiled"
    if not care.supports.issuperset(cocoon.needs):
        return "waiting"
    if params.wait_days >= PATIENCE_GOAL:
        return "transformed"
    return "waiting"


def explain_shelter(cocoon: CocoonKind, shelter: Shelter) -> str:
    missing = sorted(cocoon.needs - shelter.provides)
    return (
        f"(No story: {shelter.phrase} does not give the {cocoon.label} cocoon what it needs. "
        f"It is missing {', '.join(missing)}, so the transformation would not have an honest chance.)"
    )


def explain_care(care_id: str) -> str:
    care = CARE_METHODS[care_id]
    return (
        f"(Refusing care '{care_id}': {care.label} is too rough for this world. "
        f"A tall-tale curiosity story here prefers patient, gentle watching over damage.)"
    )


def predict_outcome(world: World, care: CareMethod, wait_days: int) -> dict:
    sim = world.copy()
    cocoon = sim.get("cocoon")
    if care.damages:
        cocoon.meters["damaged"] += 1
    if care.gentle:
        cocoon.meters["gentle_touch"] += 1
    for need in sorted(care.supports):
        cocoon.attrs["care_support"][need] = True
    cocoon.meters["patience"] += float(wait_days)
    if sim.facts["shelter_ok"]:
        cocoon.meters["sheltered"] += 1
    propagate(sim, narrate=False)
    return {
        "damaged": cocoon.meters["damaged"] >= THRESHOLD,
        "transformed": cocoon.meters["transformed"] >= THRESHOLD,
        "waiting": cocoon.meters["transformed"] < THRESHOLD and cocoon.meters["damaged"] < THRESHOLD,
    }


def opening(world: World, tribe: Tribe, hero: Entity, elder: Entity, cocoon: CocoonKind) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In the {tribe.label} tribe, where {tribe.boast}, {hero.id} was the kind of "
        f"child who could hear a secret in a leaf. One bright morning at {tribe.place}, "
        f"{hero.pronoun()} walked beside {elder.label_word} and saw {cocoon.phrase} hanging "
        f"from a branch {tribe.camp_image}."
    )
    world.say(
        f"It was so large that, in the way of tall tales, it looked almost big enough "
        f"to hide a drum inside. The children of the tribe called any strange crawling thing "
        f'''a cootie, so {hero.id} whispered, \"Is that the biggest cootie in the world?\"'''
    )


def curiosity(world: World, hero: Entity, cocoon: CocoonKind) -> None:
    hero.memes["curiosity"] += 1
    cocoon.memes["mystery"] += 1
    world.say(
        f"The cocoon did not answer, of course, but it gave a tiny {cocoon.glow}, and that "
        f"was enough to hook {hero.id}'s curiosity like a fish on a silver line."
    )
    world.say(
        f'"What is inside it?" {hero.id} asked. "{cocoon.hatch_noun.capitalize()}? '
        f'Feathers? Thunder?"'
    )


def elder_warning(world: World, elder: Entity, hero: Entity, cocoon: CocoonKind, shelter: Shelter) -> None:
    pred = predict_outcome(world, CARE_METHODS[world.facts["care"]], world.facts["wait_days"])
    world.facts["predicted_transformed"] = pred["transformed"]
    world.facts["predicted_damaged"] = pred["damaged"]
    if pred["damaged"]:
        elder.memes["concern"] += 1
        world.say(
            f'{elder.label_word.capitalize()} laid a calm hand on {hero.id}\'s shoulder. '
            f'"Not every mystery wants to be grabbed," {elder.pronoun()} said. '
            f'"If you tear it open, you may stop the change hiding inside."'
        )
    else:
        world.say(
            f'{elder.label_word.capitalize()} studied the cocoon and nodded toward {shelter.phrase}. '
            f'"Some changes need {", ".join(sorted(cocoon.needs))}," {elder.pronoun()} said. '
            f'"If we give it that and watch with quiet eyes, the answer may come out by itself."'
        )


def choose_care(world: World, hero: Entity, elder: Entity, care: CareMethod, shelter: Shelter) -> None:
    hero.memes["decision"] += 1
    world.say(care.opening_line.format(hero=hero.id, elder=elder.label_word, shelter=shelter.label))
    world.say(care.try_line.format(hero=hero.id))
    if care.damages:
        world.get("cocoon").meters["damaged"] += 1
        hero.memes["guilt"] += 1
        hero.memes["curiosity"] += 1
    if care.gentle:
        world.get("cocoon").meters["gentle_touch"] += 1
        hero.memes["care"] += 1
    propagate(world, narrate=False)


def settle_cocoon(world: World, cocoon_cfg: CocoonKind, shelter: Shelter) -> None:
    cocoon = world.get("cocoon")
    if world.facts["shelter_ok"]:
        cocoon.meters["sheltered"] += 1
        for need in cocoon_cfg.needs:
            cocoon.attrs["shelter_support"][need] = True
        world.say(
            f"They tucked the cocoon into {shelter.phrase}, {shelter.image}, and the whole little "
            f"nest looked as if it had been waiting there since the moon was a seed."
        )
    else:
        world.say(
            f"They set the cocoon in {shelter.phrase}, but even a child could feel it was not the "
            f"right sort of place for such a strange bit of living silk."
        )


def wait_and_watch(world: World, hero: Entity, elder: Entity, wait_days: int, cocoon: CocoonKind) -> None:
    cocoon_ent = world.get("cocoon")
    if wait_days <= 0:
        world.say(
            f"But {hero.id} did not wait even one full day. {hero.pronoun().capitalize()} kept peeking so fast "
            f"that the sun hardly had time to cross the sky."
        )
        return
    if wait_days == 1:
        world.say(
            f"For one long day, {hero.id} and {elder.label_word} watched from {world.facts['tribe_cfg'].watcher_spot}. "
            f"Every hour felt as tall as a pine tree, but {hero.id} kept {hero.pronoun('possessive')} hands gentle."
        )
    else:
        world.say(
            f"For {wait_days} long days, {hero.id} and {elder.label_word} watched from {world.facts['tribe_cfg'].watcher_spot}. "
            f"Each day felt big enough to have its own weather, and still {hero.id} waited."
        )
    cocoon_ent.meters["patience"] += float(wait_days)
    hero.memes["patience"] += float(wait_days)
    propagate(world, narrate=False)
    if cocoon_ent.meters["transformed"] < THRESHOLD and cocoon_ent.meters["damaged"] < THRESHOLD:
        world.say(
            f"Now and then the cocoon gave a tiny {cocoon.opening}, as if the secret inside were stretching "
            f"one sleepy elbow and then curling up again."
        )


def transformed_ending(world: World, hero: Entity, elder: Entity, cocoon: CocoonKind) -> None:
    world.say(
        f"On the last morning, the casing split with {cocoon.opening}, and out came {cocoon.transformed_phrase}. "
        f"It opened itself wider and wider until it seemed large enough to fan smoke from every cooking fire in the tribe at once."
    )
    world.say(
        f'{hero.id} laughed so hard that {hero.pronoun("possessive")} knees nearly forgot their job. '
        f'"It was never a cootie at all," {hero.pronoun()} cried.'
    )
    world.say(
        f'{elder.label_word.capitalize()} smiled. "{elder.attrs["lesson"]}," {elder.pronoun()} said. '
        f"And the {cocoon.transformed_label} lifted into the air, leaving behind one shining shell to prove the change was real."
    )


def waiting_ending(world: World, hero: Entity, elder: Entity, cocoon: CocoonKind) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"By sunset the cocoon had not opened yet, but it had grown warmer and brighter, and that was marvel enough for one story. "
        f"{hero.id} decided that some answers walk slowly before they fly."
    )
    world.say(
        f'{elder.label_word.capitalize()} nodded. "{elder.attrs["lesson"]}," {elder.pronoun()} said. '
        f"So they left the cocoon safe for another dawn, and {hero.id} walked home taller with patience than with pride."
    )


def spoiled_ending(world: World, hero: Entity, elder: Entity, cocoon: CocoonKind) -> None:
    hero.memes["sadness"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"But the casing sagged where it had been hurt, and no marvelous creature came out. The whole branch seemed to hold its breath."
    )
    world.say(
        f'{hero.id} looked at {hero.pronoun("possessive")} hands and understood that curiosity can be sharp enough to spoil what it wants to know. '
        f'{elder.label_word.capitalize()} drew {hero.pronoun("object")} close and said, "{elder.attrs["lesson"]}."'
    )
    world.say(
        f"After that, whenever the tribe children shouted \"cootie!\" at some odd little living thing, {hero.id} was the first to answer, "
        f'''\"Maybe it is changing. Let it have its chance.\"'''
    )

def tell(
    hero_name: str,
    hero_type: HeroType,
    wait_days: WaitDays,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_cfg.type, label=elder_cfg.title, role="elder"))
    cocoon = world.add(Entity(id="cocoon", kind="thing", type="cocoon", label=cocoon_cfg.label, role="mystery"))
    shelter = world.add(Entity(id="shelter", kind="thing", type="shelter", label=shelter_cfg.label, role="shelter"))

    hero.attrs["display_name"] = hero_name
    elder.attrs["lesson"] = elder_cfg.advice
    cocoon.attrs["care_support"] = {need: False for need in cocoon_cfg.needs}
    cocoon.attrs["shelter_support"] = {need: False for need in cocoon_cfg.needs}

    cocoon.meters["damaged"] = 0.0
    cocoon.meters["gentle_touch"] = 0.0
    cocoon.meters["sheltered"] = 0.0
    cocoon.meters["patience"] = 0.0
    cocoon.meters["ready"] = 0.0
    cocoon.meters["transformed"] = 0.0

    hero.memes["curiosity"] = 0.0
    hero.memes["care"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["patience"] = 0.0
    hero.memes["guilt"] = 0.0
    hero.memes["sadness"] = 0.0
    elder.memes["concern"] = 0.0
    elder.memes["pride"] = 0.0
    cocoon.memes["mystery"] = 0.0
    cocoon.memes["startled"] = 0.0

    world.facts["tribe_cfg"] = tribe_cfg
    world.facts["cocoon_cfg"] = cocoon_cfg
    world.facts["shelter_cfg"] = shelter_cfg
    world.facts["care_cfg"] = care_cfg
    world.facts["elder_cfg"] = elder_cfg
    world.facts["care"] = care_cfg.id
    world.facts["wait_days"] = wait_days
    world.facts["shelter_ok"] = shelter_works(cocoon_cfg, shelter_cfg)

    opening(world, tribe_cfg, hero, elder, cocoon_cfg)
    curiosity(world, hero, cocoon_cfg)

    world.para()
    elder_warning(world, elder, hero, cocoon_cfg, shelter_cfg)
    choose_care(world, hero, elder, care_cfg, shelter_cfg)
    settle_cocoon(world, cocoon_cfg, shelter_cfg)

    world.para()
    wait_and_watch(world, hero, elder, wait_days, cocoon_cfg)

    outcome = outcome_of(
        StoryParams(
            tribe=tribe_cfg.id,
            cocoon=cocoon_cfg.id,
            shelter=shelter_cfg.id,
            care=care_cfg.id,
            elder=elder_cfg.id,
            hero_name=hero_name,
            hero_type=hero_type,
            wait_days=wait_days,
            seed=None,
        )
    )
    if outcome == "transformed":
        world.para()
        transformed_ending(world, hero, elder, cocoon_cfg)
    elif outcome == "waiting":
        world.para()
        waiting_ending(world, hero, elder, cocoon_cfg)
    else:
        world.para()
        spoiled_ending(world, hero, elder, cocoon_cfg)

    world.facts.update(
        hero=hero,
        elder=elder,
        cocoon=cocoon,
        shelter=shelter,
        outcome=outcome,
        transformed=cocoon.meters["transformed"] >= THRESHOLD,
        damaged=cocoon.meters["damaged"] >= THRESHOLD,
    )
    return world
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


TRIBES = {
    "river_reed": Tribe(
        id="river_reed",
        label="River Reed",
        place="the bend of a silver river",
        boast="the fish were said to jump straight into breakfast bowls when they heard the drums",
        camp_image="near the cooking fires and the woven reed boats",
        watcher_spot="a smooth log beside the water",
        tags={"river", "tribe"},
    ),
    "sun_hill": Tribe(
        id="sun_hill",
        label="Sun Hill",
        place="the windy side of a high yellow hill",
        boast="the children said a shout from there could wrinkle a cloud",
        camp_image="above the ring of hide tents",
        watcher_spot="a warm stone near the berry racks",
        tags={"hill", "tribe"},
    ),
    "cedar_smoke": Tribe(
        id="cedar_smoke",
        label="Cedar Smoke",
        place="a cedar grove where the air always smelled like stories",
        boast="the grandmothers claimed even the smoke curled itself into listening shapes",
        camp_image="between cedar trunks and hanging bundles of herbs",
        watcher_spot="a stump polished by many patient watchers",
        tags={"cedar", "tribe"},
    ),
}

COCOONS = {
    "moon_moth": CocoonKind(
        id="moon_moth",
        label="moon moth",
        phrase="a striped moon-moth cocoon, fat as a soup bowl",
        casing="silk",
        hatch_noun="a moth",
        transformed_label="moon moth",
        transformed_phrase="a moon moth with pale wings wide as canoe paddles",
        habitat="branch",
        needs={"shade", "stillness"},
        glow="silver shimmer",
        opening="a careful silver crackle",
        tags={"moth", "transformation"},
    ),
    "thunder_beetle": CocoonKind(
        id="thunder_beetle",
        label="thunder beetle",
        phrase="a thunder-beetle cocoon, knuckly as a carved rattle",
        casing="amber shell",
        hatch_noun="a beetle",
        transformed_label="thunder beetle",
        transformed_phrase="a thunder beetle whose shell flashed blue like storm light",
        habitat="hollow",
        needs={"warmth", "stillness"},
        glow="blue blink",
        opening="a stout little pop",
        tags={"beetle", "transformation"},
    ),
    "whistle_wing": CocoonKind(
        id="whistle_wing",
        label="whistle-wing",
        phrase="a whistle-wing chrysalis, green as a curled leaf and long as a spoon",
        casing="leafy skin",
        hatch_noun="a winged thing",
        transformed_label="whistle-wing",
        transformed_phrase="a whistle-wing bird-moth with feathers thin as grass blades",
        habitat="leaf",
        needs={"shade", "warmth"},
        glow="green wink",
        opening="a rustly little split",
        tags={"bird_moth", "transformation"},
    ),
}

SHELTERS = {
    "reed_basket": Shelter(
        id="reed_basket",
        label="reed basket",
        phrase="a reed basket lined with soft grass",
        provides={"shade", "stillness"},
        image="with the shadows crossing it in neat stripes",
        tags={"basket", "shade"},
    ),
    "warm_stone_nook": Shelter(
        id="warm_stone_nook",
        label="warm stone nook",
        phrase="a warm stone nook tucked beside the fire pit",
        provides={"warmth", "stillness"},
        image="while the heat of the day stayed in the rock",
        tags={"stone", "warmth"},
    ),
    "leaf_tent": Shelter(
        id="leaf_tent",
        label="leaf tent",
        phrase="a leaf tent woven under a broad branch",
        provides={"shade", "warmth"},
        image="with sun and shadow trading places on its green roof",
        tags={"leaf", "warmth", "shade"},
    ),
    "windy_post": Shelter(
        id="windy_post",
        label="windy post",
        phrase="a windy post at the edge of camp",
        provides={"air"},
        image="where everything swung and knocked",
        tags={"wind"},
    ),
}

CARE_METHODS = {
    "watch_softly": CareMethod(
        id="watch_softly",
        label="watch softly",
        gentle=True,
        supports={"stillness"},
        damages=False,
        opening_line="{hero} crouched beside the cocoon and decided not to grab first.",
        try_line='"I will watch softly and let the secret keep its shell," {hero} said.',
        help_line="watched without poking",
        qa_line="watched it gently without poking it",
        tags={"gentle", "patience"},
    ),
    "hum_warm_song": CareMethod(
        id="hum_warm_song",
        label="hum a warm song",
        gentle=True,
        supports={"warmth", "stillness"},
        damages=False,
        opening_line="{hero} folded both hands and listened to {elder}'s breathing until quiet filled the space around the cocoon.",
        try_line='"Maybe a warm little song will help it feel safe," {hero} said.',
        help_line="kept the place warm and calm",
        qa_line="kept it warm and calm with a quiet song",
        tags={"gentle", "warmth"},
    ),
    "hang_shade_charm": CareMethod(
        id="hang_shade_charm",
        label="hang a shade charm",
        gentle=True,
        supports={"shade", "stillness"},
        damages=False,
        opening_line="{hero} braided a tiny shade charm from grass and tied it above the cocoon so the bright sun would not stare too hard.",
        try_line='"Now it can rest without squinting," {hero} said.',
        help_line="gave it shade and calm",
        qa_line="gave it shade and calm",
        tags={"gentle", "shade"},
    ),
    "pry_open": CareMethod(
        id="pry_open",
        label="pry it open",
        gentle=False,
        supports=set(),
        damages=True,
        opening_line="{hero} leaned in too close, sure that fast fingers could outrun a mystery.",
        try_line='"I just want one peek," {hero} said, and reached to pry the shell apart.',
        help_line="hurt the cocoon while trying to look inside",
        qa_line="tried to pry it open",
        tags={"rough"},
    ),
}

ELDERS = {
    "grandmother": Elder(
        id="grandmother",
        type="grandmother",
        title="Grandmother",
        advice="Curiosity is strongest when it learns to hold still",
        tags={"elder", "family"},
    ),
    "grandfather": Elder(
        id="grandfather",
        type="grandfather",
        title="Grandfather",
        advice="A gentle question hears more than a grabbing hand",
        tags={"elder", "family"},
    ),
    "aunt": Elder(
        id="aunt",
        type="aunt",
        title="Aunt Sela",
        advice="Some answers are alive, so they must be treated kindly",
        tags={"elder", "family"},
    ),
}

GIRL_NAMES = ["Tala", "Mira", "Nima", "Suni", "Kaya", "Luma", "Rina"]
BOY_NAMES = ["Toma", "Kio", "Raku", "Danu", "Palo", "Sami", "Leko"]
TRAITS = ["curious", "bright", "restless", "eager", "careful"]


KNOWLEDGE = {
    "tribe": [
        (
            "What is a tribe?",
            "A tribe is a community of families who live together and share stories, work, and traditions. People in a tribe help teach one another how to live well.",
        )
    ],
    "cootie": [
        (
            "What does cootie mean in this story?",
            "In this story, cootie is a teasing word the children use for a strange little crawling or wriggling thing. It does not mean the cocoon is bad; it only means the children do not understand it yet.",
        )
    ],
    "cocoon": [
        (
            "What is a cocoon?",
            "A cocoon is a protective covering some creatures make around themselves while they change. It is like a tiny room where transformation can happen.",
        )
    ],
    "transformation": [
        (
            "What is a transformation?",
            "A transformation is a big change from one form into another. A creature may look plain or quiet first and then come out looking completely different.",
        )
    ],
    "patience": [
        (
            "Why does patience matter when watching a living thing change?",
            "Patience matters because living things change in their own time. If you rush them or hurt them, the change may stop.",
        )
    ],
    "gentle": [
        (
            "Why should you be gentle with small living things?",
            "Small living things can be hurt easily. Gentle hands give them a better chance to stay safe and keep growing.",
        )
    ],
    "shade": [
        (
            "Why can shade help a small living thing?",
            "Shade can keep something from getting too hot and dry. It can also make a quiet resting place.",
        )
    ],
    "warmth": [
        (
            "Why can warmth help some tiny creatures?",
            "Warmth can help some tiny creatures stay active and keep changing. Too little warmth can make them weak or slow.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "tribe",
    "cootie",
    "cocoon",
    "transformation",
    "patience",
    "gentle",
    "shade",
    "warmth",
]


def generation_prompts(world: World) -> list[str]:
    tribe = world.facts["tribe_cfg"]
    cocoon = world.facts["cocoon_cfg"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    outcome = world.facts["outcome"]
    if outcome == "spoiled":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that includes the words "tribe" and "cootie" and is about curiosity that becomes too rough.',
            f"Tell a story where {hero.attrs['display_name']} from the {tribe.label} tribe wants to know what is inside a strange {cocoon.label} cocoon, but learns that living mysteries can be spoiled by grabbing.",
            f"Write a gentle cautionary tale in which {elder.label_word} teaches that curiosity needs kindness when a child finds something the tribe children call a cootie.",
        ]
    if outcome == "waiting":
        return [
            f'Write a tall-tale story that uses the words "tribe" and "cootie" and shows a child learning patient curiosity.',
            f"Tell a story where {hero.attrs['display_name']} finds a strange cocoon, wonders if it is a giant cootie, and learns to wait for the answer with {elder.label_word}.",
            f"Write a child-facing story about curiosity, patience, and a transformation that has begun but is not finished yet.",
        ]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the words "tribe" and "cootie" and ends with a marvelous transformation.',
        f"Tell a story where {hero.attrs['display_name']} from the {tribe.label} tribe finds a cocoon so odd the children call it a cootie, then learns that gentle curiosity reveals its secret.",
        f"Write a simple tall tale in which a child cares for a mysterious cocoon and sees what it becomes instead of tearing it open.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    cocoon = world.facts["cocoon_cfg"]
    shelter = world.facts["shelter_cfg"]
    care = world.facts["care_cfg"]
    tribe = world.facts["tribe_cfg"]
    outcome = world.facts["outcome"]
    name = hero.attrs["display_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child from the {tribe.label} tribe, and {elder.label_word}, who helps {hero.pronoun('object')} think carefully about a strange cocoon.",
        ),
        (
            f"Why did {name} call the cocoon a cootie?",
            f"{name} used the word cootie because the tribe children said that whenever they found some odd little wriggling or crawling mystery. The name shows that {name} did not understand it yet and wanted to know more.",
        ),
        (
            f"What made {name} so curious?",
            f"The cocoon looked enormous and gave a tiny {cocoon.glow}, so it felt full of secret life. That odd little sign made {name} want to know what was hidden inside.",
        ),
        (
            f"How did {elder.label_word} help {name}?",
            f"{elder.label_word.capitalize()} did not laugh at the question. {elder.pronoun().capitalize()} guided {name} toward {care.qa_line} and using {shelter.phrase} so the mystery had a fair chance to change.",
        ),
    ]
    if outcome == "transformed":
        qa.append(
            (
                "What happened at the end of the story?",
                f"The cocoon opened and turned out to hold {cocoon.transformed_phrase}. The ending proves that patient, gentle curiosity helped {name} see the transformation instead of spoiling it.",
            )
        )
    elif outcome == "waiting":
        qa.append(
            (
                "Did the cocoon transform yet?",
                f"Not yet. But it grew warmer and brighter, which showed that change was still happening inside and that waiting kindly was part of the story's answer.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the transformation fail?",
                f"It failed because {name} tried to be too fast and rough with the cocoon. The shell was hurt before the change was finished, so no creature could safely come out.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tribe", "cootie", "cocoon", "transformation", "gentle", "patience"}
    care = world.facts["care_cfg"]
    shelter = world.facts["shelter_cfg"]
    if "shade" in care.supports or "shade" in shelter.provides:
        tags.add("shade")
    if "warmth" in care.supports or "warmth" in shelter.provides:
        tags.add("warmth")
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    tribe: str
    cocoon: str
    shelter: str
    care: str
    elder: str
    hero_name: str
    hero_type: str
    wait_days: int = 2
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        tribe="river_reed",
        cocoon="moon_moth",
        shelter="reed_basket",
        care="hang_shade_charm",
        elder="grandmother",
        hero_name="Tala",
        hero_type="girl",
        wait_days=2,
        seed=None,
    ),
    StoryParams(
        tribe="sun_hill",
        cocoon="thunder_beetle",
        shelter="warm_stone_nook",
        care="hum_warm_song",
        elder="grandfather",
        hero_name="Kio",
        hero_type="boy",
        wait_days=2,
        seed=None,
    ),
    StoryParams(
        tribe="cedar_smoke",
        cocoon="whistle_wing",
        shelter="leaf_tent",
        care="watch_softly",
        elder="aunt",
        hero_name="Mira",
        hero_type="girl",
        wait_days=1,
        seed=None,
    ),
    StoryParams(
        tribe="river_reed",
        cocoon="moon_moth",
        shelter="reed_basket",
        care="pry_open",
        elder="grandmother",
        hero_name="Danu",
        hero_type="boy",
        wait_days=0,
        seed=None,
    ),
]


ASP_RULES = r"""
needs_ok(C,S) :- cocoon(C), shelter(S), not missing_need(C,S).
missing_need(C,S) :- needs(C,N), not provides(S,N).

valid(T,C,S) :- tribe(T), cocoon(C), shelter(S), needs_ok(C,S).

reasonable_care(M) :- care(M), gentle(M), not damages(M).

outcome(spoiled) :- chosen_care(M), damages(M).
outcome(spoiled) :- chosen_care(M), not gentle(M).

support_ok :- chosen_care(M), chosen_cocoon(C), not lacking_support(M,C).
lacking_support(M,C) :- needs(C,N), not supports(M,N).

enough_wait :- wait_days(D), patience_goal(P), D >= P.

outcome(transformed) :- not outcome(spoiled), shelter_ok, support_ok, enough_wait.
outcome(waiting) :- not outcome(spoiled), shelter_ok, support_ok, not enough_wait.

shelter_ok :- chosen_cocoon(C), chosen_shelter(S), needs_ok(C,S).

#show valid/3.
#show reasonable_care/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tribe_id in TRIBES:
        lines.append(asp.fact("tribe", tribe_id))
    for cocoon_id, cocoon in COCOONS.items():
        lines.append(asp.fact("cocoon", cocoon_id))
        for need in sorted(cocoon.needs):
            lines.append(asp.fact("needs", cocoon_id, need))
    for shelter_id, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", shelter_id))
        for provide in sorted(shelter.provides):
            lines.append(asp.fact("provides", shelter_id, provide))
    for care_id, care in CARE_METHODS.items():
        lines.append(asp.fact("care", care_id))
        if care.gentle:
            lines.append(asp.fact("gentle", care_id))
        if care.damages:
            lines.append(asp.fact("damages", care_id))
        for support in sorted(care.supports):
            lines.append(asp.fact("supports", care_id, support))
    lines.append(asp.fact("patience_goal", PATIENCE_GOAL))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_reasonable_care() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(c for (c,) in asp.atoms(model, "reasonable_care"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cocoon", params.cocoon),
            asp.fact("chosen_shelter", params.shelter),
            asp.fact("chosen_care", params.care),
            asp.fact("wait_days", params.wait_days),
        ]
    )
    model = asp.one_model(asp_program(extra))
    outs = [o for (o,) in asp.atoms(model, "outcome")]
    if not outs:
        return "invalid"
    return sorted(outs)[0]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a tribe child, a cootie cocoon, curiosity, and transformation."
    )
    ap.add_argument("--tribe", choices=TRIBES)
    ap.add_argument("--cocoon", choices=COCOONS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--care", choices=CARE_METHODS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--wait-days", type=int, choices=[0, 1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cocoon and args.shelter:
        cocoon = COCOONS[args.cocoon]
        shelter = SHELTERS[args.shelter]
        if not shelter_works(cocoon, shelter):
            raise StoryError(explain_shelter(cocoon, shelter))
    if args.care and args.care == "pry_open":
        # Explicitly allow this one because the world includes a cautionary branch.
        pass
    if args.care and args.care not in CARE_METHODS:
        raise StoryError("(No story: unknown care method.)")

    combos = [
        combo
        for combo in valid_combos()
        if (args.tribe is None or combo[0] == args.tribe)
        and (args.cocoon is None or combo[1] == args.cocoon)
        and (args.shelter is None or combo[2] == args.shelter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    tribe_id, cocoon_id, shelter_id = rng.choice(sorted(combos))
    care_choices = sorted(CARE_METHODS)
    if args.care is not None:
        care_id = args.care
    else:
        care_id = rng.choice(care_choices)
    elder_id = args.elder or rng.choice(sorted(ELDERS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    wait_days = args.wait_days if args.wait_days is not None else rng.choice([1, 2, 2, 3, 0])
    return StoryParams(
        tribe=tribe_id,
        cocoon=cocoon_id,
        shelter=shelter_id,
        care=care_id,
        elder=elder_id,
        hero_name=hero_name,
        hero_type=hero_type,
        wait_days=wait_days,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.tribe not in TRIBES:
        raise StoryError(f"(No story: unknown tribe '{params.tribe}'.)")
    if params.cocoon not in COCOONS:
        raise StoryError(f"(No story: unknown cocoon '{params.cocoon}'.)")
    if params.shelter not in SHELTERS:
        raise StoryError(f"(No story: unknown shelter '{params.shelter}'.)")
    if params.care not in CARE_METHODS:
        raise StoryError(f"(No story: unknown care method '{params.care}'.)")
    if params.elder not in ELDERS:
        raise StoryError(f"(No story: unknown elder '{params.elder}'.)")
    cocoon = COCOONS[params.cocoon]
    shelter = SHELTERS[params.shelter]
    if not shelter_works(cocoon, shelter):
        raise StoryError(explain_shelter(cocoon, shelter))
    world = tell(
        TRIBES[params.tribe],
        cocoon,
        shelter,
        CARE_METHODS[params.care],
        ELDERS[params.elder],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        wait_days=params.wait_days,
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
    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: valid combo gate matches ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_care = {cid for cid, care in CARE_METHODS.items() if care_is_reasonable(care)}
    clingo_care = set(asp_reasonable_care())
    if python_care == clingo_care:
        print(f"OK: reasonable care matches ({sorted(python_care)}).")
    else:
        rc = 1
        print(f"MISMATCH in reasonable care: python={sorted(python_care)} clingo={sorted(clingo_care)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp_res = asp_outcome(params)
        if py != asp_res:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(
            StoryParams(
                tribe="river_reed",
                cocoon="moon_moth",
                shelter="reed_basket",
                care="hang_shade_charm",
                elder="grandmother",
                hero_name="Tala",
                hero_type="girl",
                wait_days=2,
                seed=123,
            )
        )
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        if not smoke.prompts or not smoke.story_qa or not smoke.world_qa:
            raise StoryError("(Smoke test failed: missing prompts or QA.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        care = asp_reasonable_care()
        print(f"reasonable care: {', '.join(care)}\n")
        print(f"{len(combos)} compatible (tribe, cocoon, shelter) combos:\n")
        for tribe_id, cocoon_id, shelter_id in combos:
            print(f"  {tribe_id:12} {cocoon_id:14} {shelter_id}")
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
            header = f"### {p.hero_name}: {p.cocoon} in {p.shelter} ({p.tribe}, {p.care}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
