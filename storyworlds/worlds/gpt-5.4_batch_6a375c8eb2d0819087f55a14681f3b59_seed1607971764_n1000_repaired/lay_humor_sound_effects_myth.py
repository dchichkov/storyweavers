#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lay_humor_sound_effects_myth.py
==========================================================

A standalone story world for a tiny mythic comedy: a child in a sky temple must
lay a sacred noisemaker on the proper stand and wake the sleepy dawn. The tale
is playful and child-facing, with mythic images, sound effects, and a state-
driven turn.

The world model tracks:
- physical meters: steadiness, sounded, volume, awake, wobble, mess
- emotional memes: pride, worry, embarrassment, relief, joy

The key reasonableness constraint is simple and concrete:
a sacred relic can only be laid on supports that actually fit its shape.
A round gong needs a ring stand, a shell horn belongs on a cloud hook, and a
sun drum sits on a stone table. Invalid explicit choices raise StoryError with
a plain explanation.

The story itself then varies over:
- which relic is used
- which proper support it is laid on
- how hard the child sounds it
- which helper is nearby
- how sleepy the dawn is

Run it
------
python storyworlds/worlds/gpt-5.4/lay_humor_sound_effects_myth.py
python storyworlds/worlds/gpt-5.4/lay_humor_sound_effects_myth.py --relic gong --support ring_stand
python storyworlds/worlds/gpt-5.4/lay_humor_sound_effects_myth.py --relic horn --support stone_table
python storyworlds/worlds/gpt-5.4/lay_humor_sound_effects_myth.py --all
python storyworlds/worlds/gpt-5.4/lay_humor_sound_effects_myth.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/lay_humor_sound_effects_myth.py --asp
python storyworlds/worlds/gpt-5.4/lay_humor_sound_effects_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "goddess", "mother", "aunt"}
        male = {"boy", "man", "god", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Registries
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
class Relic:
    id: str
    label: str
    phrase: str
    shape: str
    base_sound: int
    sound_word: str
    lay_line: str
    opening_image: str
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
class Support:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
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
class Force:
    id: str
    label: str
    power: int
    gesture: str
    effect_word: str
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
    label: str
    type: str
    echo_boost: int
    calm_power: int
    entrance: str
    fix_soft: str
    fix_loud: str
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
class DawnMood:
    id: str
    label: str
    need: int
    image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_ready(world: World) -> list[str]:
    relic = world.get("relic")
    support = world.get("support")
    if relic.attrs.get("shape") in support.attrs.get("fits", set()):
        sig = ("ready", relic.id, support.id)
        if sig not in world.fired and relic.meters["laid"] >= THRESHOLD:
            world.fired.add(sig)
            relic.meters["steady"] += 1
    return []


def _r_sound(world: World) -> list[str]:
    relic = world.get("relic")
    dawn = world.get("dawn")
    if relic.meters["sounded"] < THRESHOLD or relic.meters["steady"] < THRESHOLD:
        return []
    sig = ("sound", relic.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    volume = relic.attrs["base_sound"] + int(relic.attrs["force_power"])
    world.get("temple").meters["volume"] += float(volume)
    if volume >= dawn.attrs["need"]:
        dawn.meters["awake"] += 1
    if volume >= relic.attrs["chaos_line"]:
        relic.meters["wobble"] += 1
        world.get("temple").meters["mess"] += 1
    world.get("hero").memes["pride"] += 1
    return []


def _r_embarrass(world: World) -> list[str]:
    relic = world.get("relic")
    hero = world.get("hero")
    if relic.meters["wobble"] < THRESHOLD:
        return []
    sig = ("embarrassed", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["embarrassment"] += 1
    hero.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="sound", tag="physical", apply=_r_sound),
    Rule(name="embarrass", tag="emotional", apply=_r_embarrass),
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
            else:
                before = len(world.fired)
                if rule.apply is _r_ready or rule.apply is _r_sound or rule.apply is _r_embarrass:
                    pass
                after = len(world.fired)
                if after > before:
                    changed = True
    if narrate:
        for text in produced:
            world.say(text)
    return produced


# ---------------------------------------------------------------------------
# Constraints / outcome logic
# ---------------------------------------------------------------------------
def support_fits(relic: Relic, support: Support) -> bool:
    return relic.shape in support.fits


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for relic_id, relic in RELICS.items():
        for support_id, support in SUPPORTS.items():
            if support_fits(relic, support):
                combos.append((relic_id, support_id))
    return combos


def sound_total(relic: Relic, force: Force) -> int:
    return relic.base_sound + force.power


def chaos_severity(relic: Relic, force: Force) -> int:
    total = sound_total(relic, force)
    return max(0, total - CHAOS_LINE[relic.id])


def outcome_of(params: "StoryParams") -> str:
    if params.relic not in RELICS or params.support not in SUPPORTS:
        raise StoryError("(No story: unknown relic or support.)")
    relic = RELICS[params.relic]
    support = SUPPORTS[params.support]
    if not support_fits(relic, support):
        raise StoryError(explain_rejection(relic, support))
    if params.force not in FORCES or params.helper not in HELPERS or params.dawn not in DAWNS:
        raise StoryError("(No story: unknown force, helper, or dawn mood.)")

    force = FORCES[params.force]
    helper = HELPERS[params.helper]
    dawn = DAWNS[params.dawn]
    total = sound_total(relic, force)
    if total >= dawn.need and chaos_severity(relic, force) <= helper.calm_power:
        if chaos_severity(relic, force) > 0:
            return "chaotic"
        return "smooth"
    if total < dawn.need and total + helper.echo_boost >= dawn.need:
        return "assisted"
    if total >= dawn.need and chaos_severity(relic, force) > helper.calm_power:
        return "wild"
    return "drowsy"


def explain_rejection(relic: Relic, support: Support) -> str:
    return (
        f"(No story: {relic.label} should not be laid on {support.phrase}. "
        f"It has a {relic.shape} shape and needs a support that truly holds it steady.)"
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def predict_attempt(world: World) -> dict:
    sim = world.copy()
    relic = sim.get("relic")
    relic.meters["laid"] += 1
    propagate(sim, narrate=False)
    relic.meters["sounded"] += 1
    propagate(sim, narrate=False)
    return {
        "awake": sim.get("dawn").meters["awake"] >= THRESHOLD,
        "volume": sim.get("temple").meters["volume"],
        "wobble": sim.get("relic").meters["wobble"] >= THRESHOLD,
        "mess": sim.get("temple").meters["mess"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, elder: Entity, relic: Relic, dawn: DawnMood) -> None:
    world.say(
        f"In the age when dawn still had to be coaxed over the rim of the sky, "
        f"{hero.id} served in the Cloud Temple with {elder.label}. "
        f"Below them, valleys slept under blue mist, and above them {dawn.image}."
    )
    world.say(
        f"That morning the temple had one duty: wake the dawn with {relic.phrase}. "
        f"{relic.opening_image}"
    )


def task(world: World, hero: Entity, relic: Relic, support: Support) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'"Be gentle and be true," {world.get("elder").label} said. '
        f'"First lay {relic.phrase} on {support.phrase}, and then let the sky hear it."'
    )


def climb(world: World, hero: Entity, helper: Entity, support: Support) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} climbed the pearly steps to {support.phrase}. "
        f"{helper.attrs['entrance']}"
    )


def warn(world: World, hero: Entity, helper: Entity, relic: Relic) -> None:
    pred = predict_attempt(world)
    helper.memes["concern"] += 1
    world.facts["predicted_awake"] = pred["awake"]
    world.facts["predicted_wobble"] = pred["wobble"]
    sound_note = "wake the dawn" if pred["awake"] else "barely stir the clouds"
    wobble_note = "and make it wobble with a naughty skid" if pred["wobble"] else ""
    world.say(
        f'{helper.label} peeped around a pillar and whispered, '
        f'"If you boom too boldly, it may {sound_note} {wobble_note}."'
    )


def lay_relic(world: World, hero: Entity, relic: Relic, support: Support) -> None:
    relic.meters["laid"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} nodded, took a slow breath, and lay {relic.phrase} on {support.phrase}. "
        f"{relic.lay_line}"
    )


def sound_relic(world: World, hero: Entity, relic: Relic, force: Force) -> None:
    relic.attrs["force_power"] = force.power
    relic.meters["sounded"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} {force.gesture}. {relic.sound_word}! {relic.sound_word}! "
        f"The sound rolled over the cloud roofs like golden marbles in a bowl."
    )


def smooth_dawn(world: World, hero: Entity, helper: Entity, dawn: DawnMood, relic: Relic) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At once the eastern clouds blushed. The sun sat up as if someone had tickled "
        f"its shining chin, and {dawn.label} opened its warm eye over the mountains."
    )
    world.say(
        f'{helper.label} clapped and laughed. "That was exactly enough," {helper.pronoun()} said. '
        f'Even the little swallows on the rail puffed out their chests as if they had helped.'
    )
    world.facts["ending_image"] = "the sun rose neatly over laughing clouds"
    world.facts["resolved_by"] = "hero"


def assisted_dawn(world: World, hero: Entity, helper: Entity, dawn: DawnMood, helper_cfg: HelperCfg) -> None:
    hero.memes["worry"] += 1
    helper.memes["helpfulness"] += 1
    world.say(
        f"But the dawn only stretched one rosy toe and yawned. The sky waited. "
        f"For one tiny moment, {hero.id}'s ears felt hot."
    )
    world.say(
        f"Then {helper.label} darted in and {helper_cfg.fix_soft}. "
        f"Oo-OO! The note caught the temple eaves, grew round and bright, and at last "
        f"{dawn.label} rolled awake in a ribbon of pink light."
    )
    world.say(
        f'{hero.id} laughed with relief. "{helper.label} helped the sound find its feet," '
        f"{world.get('elder').label} said, smiling."
    )
    world.facts["ending_image"] = "pink light unrolled after the helper's extra note"
    world.facts["resolved_by"] = "helper"


def chaotic_dawn(world: World, hero: Entity, helper: Entity, helper_cfg: HelperCfg, dawn: DawnMood, relic: Relic) -> None:
    hero.memes["embarrassment"] += 1
    helper.memes["helpfulness"] += 1
    world.say(
        f"The note was so grand that {relic.phrase} shivered on its stand. Skrrr-rr! "
        f"A basket of moon figs tipped over, three temple geese cried HONK! HONK! HONK!, "
        f"and one sleepy cloud bumped the bell-rope just for the fun of it."
    )
    world.say(
        f"{helper.label} sprang forward and {helper_cfg.fix_loud}. "
        f"The last wild echo curled into a polite little hum."
    )
    world.say(
        f"By then the sun was already peeking up, amused. It rose with a crooked grin, "
        f"as if even the heavens enjoyed a joke before breakfast."
    )
    world.facts["ending_image"] = "the sun rose with a crooked grin over honking geese"
    world.facts["resolved_by"] = "helper"


def wild_dawn(world: World, hero: Entity, helper: Entity, dawn: DawnMood, relic: Relic) -> None:
    hero.memes["worry"] += 1
    hero.memes["embarrassment"] += 1
    world.say(
        f"The boom ran much too far. Clouds bounced from cloud to cloud, the geese forgot "
        f"their manners, and a startled rainbow came out sideways."
    )
    world.say(
        f"Still, dawn woke in the middle of the racket. The sun rose blinking over the edge "
        f"of the world while everyone scrambled to stop laughing and tidy the figs."
    )
    world.say(
        f'{world.get("elder").label} finally sighed, then chuckled. "Tomorrow," {world.get("elder").pronoun()} said, '
        f'"we shall try less thunder and more wisdom."'
    )
    world.facts["ending_image"] = "a sideways rainbow hung above a laughing, messy temple"
    world.facts["resolved_by"] = "nobody"


def close_lesson(world: World, hero: Entity, elder: Entity, relic: Relic, support: Support, outcome: str) -> None:
    hero.memes["lesson"] += 1
    elder.memes["pride"] += 1
    if outcome == "smooth":
        world.say(
            f"{elder.label} rested a hand on {hero.id}'s shoulder. "
            f'"You laid {relic.label} well, sounded it well, and the morning listened," '
            f"{elder.pronoun()} said."
        )
    elif outcome == "assisted":
        world.say(
            f"{elder.label} bent close and smiled. "
            f'"A small sound can still do holy work when friends help it along," '
            f"{elder.pronoun()} said."
        )
    elif outcome == "chaotic":
        world.say(
            f"{elder.label} picked a moon fig out of {hero.pronoun('possessive')} sleeve and laughed. "
            f'"Next time, lay the relic steady and wake the sky without waking every goose," '
            f"{elder.pronoun()} said."
        )
    else:
        world.say(
            f"{elder.label} straightened the stand and nodded toward {support.phrase}. "
            f'"The sky forgives noise," {elder.pronoun()} said, "but it loves care even more."'
        )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    support_cfg: Support,
    force_cfg: Force,
    helper_cfg: Helper,
    dawn_cfg: Dawn,
    hero_name: str,
    hero_gender: str,
    elder_type: ElderType,
    relic_cfg=None,
) -> World:
    world = World()

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, role="hero"))
    elder_label = "Lady Lark-of-Morning" if elder_type == "goddess" else "Old Cloud-Keeper"
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_label, role="elder"))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            role="helper",
            attrs={"entrance": helper_cfg.entrance},
        )
    )
    relic = world.add(
        Entity(
            id="relic",
            type="relic",
            label=relic_cfg.label,
            attrs={
                "shape": relic_cfg.shape,
                "base_sound": relic_cfg.base_sound,
                "force_power": 0,
                "chaos_line": CHAOS_LINE[relic_cfg.id],
            },
        )
    )
    support = world.add(
        Entity(
            id="support",
            type="support",
            label=support_cfg.label,
            attrs={"fits": set(support_cfg.fits)},
        )
    )
    dawn = world.add(
        Entity(
            id="dawn",
            type="dawn",
            label=dawn_cfg.label,
            attrs={"need": dawn_cfg.need},
        )
    )
    world.add(Entity(id="temple", type="place", label="the Cloud Temple"))

    hero.memes["curiosity"] = 1.0
    helper.memes["friendliness"] = 1.0
    elder.memes["calm"] = 1.0
    relic.meters["laid"] = 0.0
    relic.meters["steady"] = 0.0
    relic.meters["sounded"] = 0.0
    relic.meters["wobble"] = 0.0
    dawn.meters["awake"] = 0.0
    world.get("temple").meters["volume"] = 0.0
    world.get("temple").meters["mess"] = 0.0

    introduce(world, hero, elder, relic_cfg, dawn_cfg)
    task(world, hero, relic_cfg, support_cfg)

    world.para()
    climb(world, hero, helper, support_cfg)
    warn(world, hero, helper, relic_cfg)
    lay_relic(world, hero, relic_cfg, support_cfg)
    sound_relic(world, hero, relic_cfg, force_cfg)

    outcome = outcome_of(
        StoryParams(
            relic=relic_cfg.id,
            support=support_cfg.id,
            force=force_cfg.id,
            helper=helper_cfg.id,
            dawn=dawn_cfg.id,
            hero=hero_name,
            gender=hero_gender,
            elder=elder_type,
            seed=None,
        )
    )

    world.para()
    if outcome == "smooth":
        smooth_dawn(world, hero, helper, dawn_cfg, relic_cfg)
    elif outcome == "assisted":
        assisted_dawn(world, hero, helper, dawn_cfg, helper_cfg)
        dawn.meters["awake"] = 1.0
    elif outcome == "chaotic":
        chaotic_dawn(world, hero, helper, helper_cfg, dawn_cfg, relic_cfg)
        dawn.meters["awake"] = 1.0
    elif outcome == "wild":
        wild_dawn(world, hero, helper, dawn_cfg, relic_cfg)
        dawn.meters["awake"] = 1.0
    else:
        assisted_dawn(world, hero, helper, dawn_cfg, helper_cfg)
        dawn.meters["awake"] = 1.0

    close_lesson(world, hero, elder, relic_cfg, support_cfg, outcome)

    world.facts.update(
        hero=hero,
        elder=elder,
        helper=helper,
        relic_cfg=relic_cfg,
        support_cfg=support_cfg,
        force_cfg=force_cfg,
        helper_cfg=helper_cfg,
        dawn_cfg=dawn_cfg,
        relic=relic,
        support=support,
        dawn=dawn,
        temple=world.get("temple"),
        outcome=outcome,
        awake=dawn.meters["awake"] >= THRESHOLD,
        volume=int(world.get("temple").meters["volume"]),
        wobble=relic.meters["wobble"] >= THRESHOLD,
        mess=world.get("temple").meters["mess"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
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


RELICS = {
    "gong": Relic(
        id="gong",
        label="the dawn gong",
        phrase="the round dawn gong",
        shape="round",
        base_sound=3,
        sound_word="BONG",
        lay_line="It settled with a shining little hum, as if it already knew the sun by name.",
        opening_image="Its face was hammered with tiny rays and laughing lions.",
        tags={"gong", "sound", "dawn"},
    ),
    "horn": Relic(
        id="horn",
        label="the moon-shell horn",
        phrase="the curling moon-shell horn",
        shape="curved",
        base_sound=2,
        sound_word="TOOO",
        lay_line="The shell gleamed pearly-white and pointed its bright mouth toward the east.",
        opening_image="Its spiral was so pale it looked borrowed from the moon.",
        tags={"horn", "shell", "sound"},
    ),
    "drum": Relic(
        id="drum",
        label="the sun drum",
        phrase="the flat sun drum",
        shape="flat",
        base_sound=2,
        sound_word="POM",
        lay_line="Its painted hide stayed still as a pond just before sunrise.",
        opening_image="Across its skin ran a ring of little red horses chasing daylight.",
        tags={"drum", "sound", "dawn"},
    ),
}

SUPPORTS = {
    "ring_stand": Support(
        id="ring_stand",
        label="the ring stand",
        phrase="the bronze ring stand",
        fits={"round"},
        tags={"stand"},
    ),
    "cloud_hook": Support(
        id="cloud_hook",
        label="the cloud hook",
        phrase="the silver cloud hook",
        fits={"curved"},
        tags={"hook"},
    ),
    "stone_table": Support(
        id="stone_table",
        label="the stone table",
        phrase="the flat stone table",
        fits={"flat"},
        tags={"table"},
    ),
}

FORCES = {
    "soft": Force(
        id="soft",
        label="softly",
        power=1,
        gesture="tapped it softly with a cedar wand",
        effect_word="soft",
        tags={"gentle"},
    ),
    "steady": Force(
        id="steady",
        label="steadily",
        power=2,
        gesture="struck a steady, brave note",
        effect_word="steady",
        tags={"careful"},
    ),
    "mighty": Force(
        id="mighty",
        label="mightily",
        power=4,
        gesture="gave it a mighty thump worthy of a giant",
        effect_word="mighty",
        tags={"loud"},
    ),
}

HELPERS = {
    "breeze_sprite": HelperCfg(
        id="breeze_sprite",
        label="Piri the Breeze Sprite",
        type="girl",
        echo_boost=2,
        calm_power=1,
        entrance="Piri the Breeze Sprite whirled after him, carrying a ribbon and a grin.",
        fix_soft="blew one neat silver breath into the note",
        fix_loud="caught the swinging stand with both hands and blew the extra boom up into the empty sky",
        tags={"wind", "helper"},
    ),
    "goat_page": HelperCfg(
        id="goat_page",
        label="Toma the Goat Page",
        type="boy",
        echo_boost=1,
        calm_power=2,
        entrance="Toma the Goat Page trotted behind, his little bells going tink-tink.",
        fix_soft="cupped his hands and added a second cheerful call",
        fix_loud="leaped onto a fig basket, grabbed the stand, and held it steady with surprising dignity",
        tags={"goat", "helper"},
    ),
    "stork_aunt": HelperCfg(
        id="stork_aunt",
        label="Aunt Sori the Stork",
        type="aunt",
        echo_boost=2,
        calm_power=3,
        entrance="Aunt Sori the Stork clicked her beak and glided beside the stair.",
        fix_soft="stretched her long beak into the breeze and sent the sound farther east",
        fix_loud="pinned the wobbling relic still with one wise foot and folded the wild echoes under her broad wing",
        tags={"stork", "helper"},
    ),
}

DAWNS = {
    "easy": DawnMood(
        id="easy",
        label="the light-bellied dawn",
        need=4,
        image="the light-bellied dawn was already blinking behind a curtain of pearl cloud",
        tags={"dawn"},
    ),
    "sleepy": DawnMood(
        id="sleepy",
        label="the sleepy dawn",
        need=5,
        image="the sleepy dawn lay under its blankets of cloud and would not yet open one golden eye",
        tags={"dawn", "sleep"},
    ),
    "stubborn": DawnMood(
        id="stubborn",
        label="the stubborn dawn",
        need=6,
        image="the stubborn dawn lay snoring beyond the mountains as if it had promised not to wake for anybody",
        tags={"dawn", "sleep"},
    ),
}

CHAOS_LINE = {
    "gong": 6,
    "horn": 7,
    "drum": 6,
}

GIRL_NAMES = ["Nera", "Lumi", "Piri", "Sela", "Mira", "Tavi"]
BOY_NAMES = ["Nilo", "Toma", "Rin", "Calo", "Davi", "Sorin"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "gong": [
        (
            "What is a gong?",
            "A gong is a round metal instrument that makes a big ringing sound when it is struck. It can be loud enough to call people from far away.",
        )
    ],
    "horn": [
        (
            "What is a shell horn?",
            "A shell horn is a hollow shell used like a trumpet. When you blow into it, the air vibrates and makes a strong note.",
        )
    ],
    "drum": [
        (
            "What is a drum?",
            "A drum is an instrument you tap or strike to make a beat. The sound comes from a stretched surface that vibrates.",
        )
    ],
    "sound": [
        (
            "Why do loud sounds travel far?",
            "Loud sounds push more strongly through the air, so people farther away can hear them. That is why bells, horns, and drums are used for signals.",
        )
    ],
    "wind": [
        (
            "How can wind help a sound?",
            "Wind can carry a sound farther by helping it move through the air. A breeze can make a note seem stronger and longer.",
        )
    ],
    "stand": [
        (
            "Why should you put an object on the right stand?",
            "The right stand keeps an object steady so it does not tip or slide. A good fit makes work safer and easier.",
        )
    ],
    "hook": [
        (
            "What is a hook for?",
            "A hook holds something by hanging it in place. It is useful for objects with a curved shape.",
        )
    ],
    "table": [
        (
            "Why is a flat table good for flat things?",
            "A flat table gives flat things even support all the way underneath. That helps them stay still.",
        )
    ],
    "dawn": [
        (
            "What is dawn?",
            "Dawn is the time when night begins to turn into morning. The sky grows lighter before the sun fully rises.",
        )
    ],
}
KNOWLEDGE_ORDER = ["gong", "horn", "drum", "sound", "wind", "stand", "hook", "table", "dawn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    relic = f["relic_cfg"]
    support = f["support_cfg"]
    helper = f["helper_cfg"]
    dawn = f["dawn_cfg"]
    return [
        f'Write a short mythic story for a 3-to-5-year-old that includes the word "lay" and uses playful sound effects.',
        f"Tell a gentle myth where {hero.id} must lay {relic.phrase} on {support.phrase} to wake {dawn.label}, with {helper.label} nearby and a funny turn in the middle.",
        f"Write a humorous dawn myth about a child temple helper, a sacred noisemaker, and the morning finally arriving.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    helper = f["helper"]
    relic_cfg = f["relic_cfg"]
    support_cfg = f["support_cfg"]
    force_cfg = f["force_cfg"]
    dawn_cfg = f["dawn_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young helper in the Cloud Temple. {elder.label} gives the task, and {helper.label} stays nearby."
        ),
        (
            "What job did the temple have that morning?",
            f"The temple had to wake {dawn_cfg.label} so morning could begin. They did it by sounding {relic_cfg.phrase}."
        ),
        (
            f"Where did {hero.id} lay the relic?",
            f"{hero.id} lay {relic_cfg.phrase} on {support_cfg.phrase}. That mattered because the support fit the relic's shape and kept it steady."
        ),
    ]

    if outcome == "smooth":
        qa.append(
            (
                f"Why did the dawn wake so quickly?",
                f"{hero.id} used {force_cfg.label} sound on a relic that was laid properly and held steady. The note was strong enough to wake the morning without causing trouble."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The sun rose neatly and everyone was pleased. The ending image shows the heavens listening because {hero.id} used care as well as courage."
            )
        )
    elif outcome == "assisted":
        qa.append(
            (
                f"Why did {helper.label} have to help?",
                f"{hero.id}'s first note was a little too small for {dawn_cfg.label}. {helper.label} added another breath or call, and together the sound reached the sleeping morning."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The dawn finally woke after the helper strengthened the sound. The ending proves that small work can still succeed when friends join in."
            )
        )
    elif outcome == "chaotic":
        qa.append(
            (
                "What funny problem happened after the sound?",
                f"The note was so big that the relic wobbled, moon figs spilled, and temple geese honked. The trouble came from making a grand sound that was just a bit too wild."
            )
        )
        qa.append(
            (
                f"How was the problem fixed?",
                f"{helper.label} quickly steadied things and tucked the extra noise away. Dawn still arrived, so the mistake turned into a joke instead of a disaster."
            )
        )
    else:
        qa.append(
            (
                "Why was the morning messy?",
                f"The boom was much louder than the temple needed, so the whole place turned noisy and silly. Even so, dawn woke up in the middle of the chaos."
            )
        )
        qa.append(
            (
                "What did the elder want the child to learn?",
                f"{elder.label} wanted {hero.id} to use more care next time. A holy job needs strength, but it also needs wisdom."
            )
        )

    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    relic_id = world.facts["relic_cfg"].id
    support_id = world.facts["support_cfg"].id
    helper_id = world.facts["helper_cfg"].id
    dawn_id = world.facts["dawn_cfg"].id

    tags.add(relic_id)
    tags.add("sound")
    if helper_id == "breeze_sprite":
        tags.add("wind")
    if support_id == "ring_stand":
        tags.add("stand")
    elif support_id == "cloud_hook":
        tags.add("hook")
    elif support_id == "stone_table":
        tags.add("table")
    if dawn_id in DAWNS:
        tags.add("dawn")

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
            shown = {k: sorted(v) if isinstance(v, set) else v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(R,S) :- relic(R), support(S), shape(R,Sh), support_shape(S,Sh).

valid(R,S) :- fits(R,S).

total_sound(R,F,T) :- base_sound(R,B), force_power(F,P), T = B + P.
chaos(R,F,C) :- total_sound(R,F,T), chaos_line(R,L), T > L, C = T - L.
chaos(R,F,0) :- total_sound(R,F,T), chaos_line(R,L), T <= L.

outcome(smooth) :-
    chosen_relic(R), chosen_force(F), chosen_helper(H), chosen_dawn(D),
    total_sound(R,F,T), dawn_need(D,N), T >= N,
    chaos(R,F,C), calm_power(H,K), C = 0.

outcome(chaotic) :-
    chosen_relic(R), chosen_force(F), chosen_helper(H), chosen_dawn(D),
    total_sound(R,F,T), dawn_need(D,N), T >= N,
    chaos(R,F,C), calm_power(H,K), C > 0, C <= K.

outcome(assisted) :-
    chosen_relic(R), chosen_force(F), chosen_helper(H), chosen_dawn(D),
    total_sound(R,F,T), dawn_need(D,N), T < N,
    echo_boost(H,E), T + E >= N.

outcome(wild) :-
    chosen_relic(R), chosen_force(F), chosen_helper(H), chosen_dawn(D),
    total_sound(R,F,T), dawn_need(D,N), T >= N,
    chaos(R,F,C), calm_power(H,K), C > K.

outcome(drowsy) :-
    chosen_relic(R), chosen_force(F), chosen_helper(H), chosen_dawn(D),
    total_sound(R,F,T), dawn_need(D,N), T < N,
    echo_boost(H,E), T + E < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("shape", rid, relic.shape))
        lines.append(asp.fact("base_sound", rid, relic.base_sound))
        lines.append(asp.fact("chaos_line", rid, CHAOS_LINE[rid]))
    for sid, support in SUPPORTS.items():
        lines.append(asp.fact("support", sid))
        for shape in sorted(support.fits):
            lines.append(asp.fact("support_shape", sid, shape))
    for fid, force in FORCES.items():
        lines.append(asp.fact("force", fid))
        lines.append(asp.fact("force_power", fid, force.power))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("echo_boost", hid, helper.echo_boost))
        lines.append(asp.fact("calm_power", hid, helper.calm_power))
    for did, dawn in DAWNS.items():
        lines.append(asp.fact("dawn", did))
        lines.append(asp.fact("dawn_need", did, dawn.need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_relic", params.relic),
            asp.fact("chosen_support", params.support),
            asp.fact("chosen_force", params.force),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_dawn", params.dawn),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    for _ in range(120):
        try:
            p = resolve_params(parser.parse_args([]), rng)
        except StoryError:
            continue
        cases.append(p)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    relic: str = "gong"
    support: str = "ring_stand"
    force: str = "steady"
    helper: str = "breeze_sprite"
    dawn: str = "sleepy"
    hero: str = "Nilo"
    gender: str = "boy"
    elder: str = "goddess"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        relic="gong",
        support="ring_stand",
        force="steady",
        helper="breeze_sprite",
        dawn="easy",
        hero="Nilo",
        gender="boy",
        elder="goddess",
    ),
    StoryParams(
        relic="horn",
        support="cloud_hook",
        force="soft",
        helper="stork_aunt",
        dawn="sleepy",
        hero="Mira",
        gender="girl",
        elder="goddess",
    ),
    StoryParams(
        relic="drum",
        support="stone_table",
        force="mighty",
        helper="goat_page",
        dawn="easy",
        hero="Rin",
        gender="boy",
        elder="god",
    ),
    StoryParams(
        relic="gong",
        support="ring_stand",
        force="mighty",
        helper="breeze_sprite",
        dawn="sleepy",
        hero="Sela",
        gender="girl",
        elder="goddess",
    ),
    StoryParams(
        relic="horn",
        support="cloud_hook",
        force="soft",
        helper="goat_page",
        dawn="stubborn",
        hero="Davi",
        gender="boy",
        elder="god",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a child must lay a sacred relic on the proper support and wake the dawn."
    )
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--force", choices=FORCES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--dawn", choices=DAWNS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["goddess", "god"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible relic/support pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.relic and args.support:
        relic = RELICS[args.relic]
        support = SUPPORTS[args.support]
        if not support_fits(relic, support):
            raise StoryError(explain_rejection(relic, support))

    combos = [
        combo
        for combo in valid_combos()
        if (args.relic is None or combo[0] == args.relic)
        and (args.support is None or combo[1] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    relic_id, support_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.hero:
        hero = args.hero
    else:
        hero = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    force = args.force or rng.choice(sorted(FORCES))
    helper = args.helper or rng.choice(sorted(HELPERS))
    dawn = args.dawn or rng.choice(sorted(DAWNS))
    elder = args.elder or rng.choice(["goddess", "god"])

    return StoryParams(
        relic=relic_id,
        support=support_id,
        force=force,
        helper=helper,
        dawn=dawn,
        hero=hero,
        gender=gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    missing = []
    if params.relic not in RELICS:
        missing.append("relic")
    if params.support not in SUPPORTS:
        missing.append("support")
    if params.force not in FORCES:
        missing.append("force")
    if params.helper not in HELPERS:
        missing.append("helper")
    if params.dawn not in DAWNS:
        missing.append("dawn")
    if missing:
        raise StoryError(f"(No story: unknown parameter(s): {', '.join(missing)}.)")

    relic = RELICS[params.relic]
    support = SUPPORTS[params.support]
    if not support_fits(relic, support):
        raise StoryError(explain_rejection(relic, support))

    world = tell(
        relic_cfg=relic,
        support_cfg=support,
        force_cfg=FORCES[params.force],
        helper_cfg=HELPERS[params.helper],
        dawn_cfg=DAWNS[params.dawn],
        hero_name=params.hero,
        hero_gender=params.gender,
        elder_type=params.elder,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (relic, support) combos:\n")
        for relic, support in combos:
            print(f"  {relic:6} {support}")
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
            header = f"### {p.hero}: {p.relic} on {p.support} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
