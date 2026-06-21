#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/millenium_chunk_flashback_fairy_tale.py
==================================================================

A standalone storyworld for a small fairy-tale domain built from the seed words
"millenium" and "chunk" with a required flashback turn.

Premise
-------
In a bright little kingdom, a child is trusted to carry an old enchanted relic
to the millenium feast. An accident chips, cracks, or tears it. The child feels
the festival is in danger, remembers an elder's earlier lesson in a flashback,
asks the right craft helper for help, and the relic is mended in time.

The world model enforces reasonableness:
- only some damage kinds fit some relic materials,
- only some fixes work on some materials,
- only some helpers can perform those repairs,
- and some repairs are stronger than others, changing the ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/millenium_chunk_flashback_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/millenium_chunk_flashback_fairy_tale.py --relic moon_bell
    python storyworlds/worlds/gpt-5.4/millenium_chunk_flashback_fairy_tale.py --damage tear
    python storyworlds/worlds/gpt-5.4/millenium_chunk_flashback_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/millenium_chunk_flashback_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/millenium_chunk_flashback_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/millenium_chunk_flashback_fairy_tale.py --asp
    python storyworlds/worlds/gpt-5.4/millenium_chunk_flashback_fairy_tale.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "princess", "mother", "grandmother", "woman", "fairy_godmother"}
        male = {"boy", "prince", "father", "grandfather", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "fairy_godmother": "godmother",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configuration
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
    material: str
    place: str
    purpose: str
    shine_word: str
    fragility: int
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
class Damage:
    id: str
    label: str
    verb_past: str
    sign: str
    severity: int
    allowed_materials: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    title: str
    place: str
    crafts: set[str] = field(default_factory=set)
    bonus: int = 0
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
class Fix:
    id: str
    label: str
    phrase: str
    materials: set[str] = field(default_factory=set)
    strength: int = 0
    action: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
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
# Rules
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


def _r_damage_threat(world: World) -> list[str]:
    relic = world.get("relic")
    kingdom = world.get("kingdom")
    hero = world.get("hero")
    if relic.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_threat", "relic")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kingdom.meters["festival_risk"] += 1
    hero.memes["worry"] += 1
    return []


def _r_memory_courage(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["remembered"] < THRESHOLD:
        return []
    sig = ("memory_courage", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    hero.memes["shame"] = max(0.0, hero.memes["shame"] - 1.0)
    return []


def _r_help_brings_hope(world: World) -> list[str]:
    hero = world.get("hero")
    kingdom = world.get("kingdom")
    if hero.memes["asked_help"] < THRESHOLD:
        return []
    sig = ("help_hope", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kingdom.memes["hope"] += 1
    hero.memes["trust"] += 1
    return []


def _r_repair_relief(world: World) -> list[str]:
    relic = world.get("relic")
    hero = world.get("hero")
    kingdom = world.get("kingdom")
    if relic.meters["repaired"] < THRESHOLD:
        return []
    sig = ("repair_relief", "relic")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kingdom.meters["festival_risk"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="damage_threat", tag="physical", apply=_r_damage_threat),
    Rule(name="memory_courage", tag="emotional", apply=_r_memory_courage),
    Rule(name="help_hope", tag="social", apply=_r_help_brings_hope),
    Rule(name="repair_relief", tag="physical", apply=_r_repair_relief),
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
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def damage_fits(relic: Relic, damage: Damage) -> bool:
    return relic.material in damage.allowed_materials


def fix_fits(relic: Relic, fix: Fix) -> bool:
    return relic.material in fix.materials


def helper_fits(helper: Helper, relic: Relic) -> bool:
    return relic.material in helper.crafts


def repair_power(helper: Helper, fix: Fix) -> int:
    return helper.bonus + fix.strength


def repair_need(relic: Relic, damage: Damage) -> int:
    return relic.fragility + damage.severity


def can_mend(relic: Relic, damage: Damage, helper: Helper, fix: Fix) -> bool:
    return (
        damage_fits(relic, damage)
        and fix_fits(relic, fix)
        and helper_fits(helper, relic)
        and repair_power(helper, fix) >= damage.severity + 1
    )


def outcome_of(params: "StoryParams") -> str:
    relic = RELICS[params.relic]
    damage = DAMAGES[params.damage]
    helper = HELPERS[params.helper]
    fix = FIXES[params.fix]
    total = repair_power(helper, fix)
    need = repair_need(relic, damage)
    return "bright" if total >= need else "mended"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for relic_id, relic in RELICS.items():
        for damage_id, damage in DAMAGES.items():
            for helper_id, helper in HELPERS.items():
                for fix_id, fix in FIXES.items():
                    if can_mend(relic, damage, helper, fix):
                        combos.append((relic_id, damage_id, helper_id, fix_id))
    return combos


def explain_rejection(relic: Relic, damage: Damage, helper: Helper, fix: Fix) -> str:
    if not damage_fits(relic, damage):
        return (
            f"(No story: {relic.label} is made of {relic.material}, but a "
            f"{damage.label} is not a sensible kind of damage for that material.)"
        )
    if not fix_fits(relic, fix):
        return (
            f"(No story: {fix.label} does not mend {relic.material} well enough "
            f"to repair {relic.label}.)"
        )
    if not helper_fits(helper, relic):
        return (
            f"(No story: {helper.title} works with {sorted(helper.crafts)}, not "
            f"{relic.material}. Choose a craft helper who can really mend it.)"
        )
    if repair_power(helper, fix) < damage.severity + 1:
        return (
            f"(No story: {helper.title} using {fix.label} would be too weak for a "
            f"{damage.label}. The repair must have a fair chance to hold.)"
        )
    return "(No story: that combination does not make a reasonable repair tale.)"


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    relic: str = "moon_bell"
    damage: str = "chip"
    helper: str = "bellsmith"
    fix: str = "star_solder"
    hero_name: str = "Lina"
    hero_gender: str = "girl"
    elder_type: str = "grandmother"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story verbs
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


def introduce(world: World, hero: Entity, elder: Entity, relic: Relic) -> None:
    world.say(
        f"Once upon a time, in a valley where foxgloves nodded beside a silver road, "
        f"there lived a little {hero.type} named {hero.id}. On the morning of the "
        f"millenium feast, {hero.id}'s {elder.label_word} trusted {hero.pronoun('object')} "
        f"with {relic.phrase}."
    )
    world.say(
        f"The old treasure belonged at {relic.place}, because its {relic.shine_word} "
        f"was meant to {relic.purpose} before moonrise."
    )


def set_out(world: World, hero: Entity, relic: Relic) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} carried the {relic.label} in both hands and walked as carefully "
        f"as a child crossing a bridge of mist."
    )


def accident(world: World, hero: Entity, relic_ent: Entity, relic: Relic, damage: Damage) -> None:
    hero.memes["shame"] += 1
    hero.memes["fear"] += 1
    relic_ent.meters["damaged"] += 1
    relic_ent.meters[damage.id] += 1
    relic_ent.attrs["damage_label"] = damage.label
    relic_ent.attrs["damage_sign"] = damage.sign
    propagate(world, narrate=False)
    if damage.id == "chip":
        world.say(
            f"But near the mossy gate, {hero.id}'s shoe caught on a root. The {relic.label} "
            f"bumped the stone path, and a little chunk broke away from its rim."
        )
    elif damage.id == "crack":
        world.say(
            f"But near the mossy gate, {hero.id} stumbled. A thin line ran over the "
            f"{relic.label} like winter ice on a pond: it had cracked."
        )
    else:
        world.say(
            f"But near the mossy gate, a thorny branch tugged at the {relic.label}. "
            f"The edge tore with a soft, unhappy sound."
        )
    world.say(
        f"{hero.id} stared at the damage. At once {hero.pronoun('possessive')} chest felt tight, "
        f"for it seemed the feast itself might dim."
    )


def flashback(world: World, hero: Entity, elder: Entity, relic: Relic) -> None:
    hero.memes["remembered"] += 1
    propagate(world, narrate=False)
    lesson = elder.attrs["lesson"]
    memory_item = elder.attrs["memory_item"]
    world.say(
        f"Then a flashback came to {hero.id} as softly as lamplight through lace. "
        f"{hero.pronoun().capitalize()} remembered a spring afternoon when {elder.label_word} "
        f"had set a damaged {memory_item} on the windowsill and said, "
        f'"{lesson}"'
    )
    world.facts["flashback_happened"] = True


def choose_truth(world: World, hero: Entity) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f"So instead of hiding the hurt, {hero.id} lifted {hero.pronoun('possessive')} chin. "
        f"If a thing was broken, the truest first step was to ask for wise hands."
    )


def seek_helper(world: World, hero: Entity, helper_ent: Entity, helper: Helper) -> None:
    hero.memes["asked_help"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} hurried to {helper.place}, where {helper.title} was awake among "
        f"warm tools and bright shavings."
    )
    world.say(
        f'"Please," said {hero.id}, "I was carrying the feast treasure, and now it is hurt. '
        f'Can you help me mend it before moonrise?"'
    )


def mend(world: World, hero: Entity, helper_ent: Entity, relic_ent: Entity,
         relic: Relic, damage: Damage, fix: Fix, helper: Helper) -> None:
    relic_ent.meters["repaired"] += 1
    relic_ent.meters["damaged"] = 0.0
    relic_ent.attrs["fix_label"] = fix.label
    relic_ent.attrs["helper_label"] = helper.title
    relic_ent.attrs["outcome"] = outcome_of(world.facts["params"])
    propagate(world, narrate=False)
    world.say(
        f"{helper.title} nodded, took out {fix.phrase}, and {fix.action}. "
        f"Bit by bit, the hurt place steadied under patient fingers."
    )


def ending(world: World, hero: Entity, elder: Entity, relic_ent: Entity, relic: Relic) -> None:
    outcome = world.facts["outcome"]
    if outcome == "bright":
        relic_ent.meters["glow"] += 1
        hero.memes["joy"] += 1
        world.say(
            f"When the relic was raised at {relic.place}, it shone even more warmly than before. "
            f"The bell-note rang true, or the glass gleamed true, or the cloth flew true, and the "
            f"whole valley seemed to breathe again."
        )
        world.say(
            f"{elder.label_word.capitalize()} squeezed {hero.id}'s shoulder. "
            f'"You were brave twice," {elder.pronoun()} said. "Once when trouble came, '
            f'and once when you told the truth."'
        )
        world.say(
            f"And from that night on, whenever {hero.id} carried something precious, "
            f"{hero.pronoun()} carried honesty with it."
        )
    else:
        relic_ent.meters["glow"] += 1
        hero.memes["joy"] += 1
        world.say(
            f"At {relic.place}, the old treasure was whole again, though a small bright seam "
            f"still showed where the hurt had been. It did not spoil the feast. It proved the "
            f"relic had been cared for with love."
        )
        world.say(
            f"{elder.label_word.capitalize()} smiled at {hero.id}. "
            f'"A careful heart can mend more than it harms," {elder.pronoun()} said.'
        )
        world.say(
            f"And so the child watched the feastlight dance over the gentle seam, and learned "
            f"that truth can leave a mark that glitters instead of hiding."
        )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    if params.relic not in RELICS:
        raise StoryError(f"(Unknown relic: {params.relic})")
    if params.damage not in DAMAGES:
        raise StoryError(f"(Unknown damage: {params.damage})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError("(hero_gender must be 'girl' or 'boy')")
    if params.elder_type not in {"grandmother", "grandfather", "fairy_godmother"}:
        raise StoryError("(elder_type must be grandmother, grandfather, or fairy_godmother)")

    relic = RELICS[params.relic]
    damage = DAMAGES[params.damage]
    helper = HELPERS[params.helper]
    fix = FIXES[params.fix]
    if not can_mend(relic, damage, helper, fix):
        raise StoryError(explain_rejection(relic, damage, helper, fix))

    world = World()
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        role="hero",
        attrs={},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=params.elder_type,
        label="the elder",
        role="elder",
        attrs={},
    ))
    helper_ent = world.add(Entity(
        id="Helper",
        kind="character",
        type="craftsperson",
        label=helper.label,
        role="helper",
        attrs={"title": helper.title},
    ))
    relic_ent = world.add(Entity(
        id="relic",
        kind="thing",
        type="relic",
        label=relic.label,
        role="relic",
        attrs={"material": relic.material},
    ))
    kingdom = world.add(Entity(
        id="kingdom",
        kind="thing",
        type="kingdom",
        label="the valley kingdom",
        role="kingdom",
        attrs={},
    ))

    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 0.0
    hero.memes["trust"] = 0.0
    hero.memes["honesty"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["shame"] = 0.0
    elder.attrs["lesson"] = "When a precious thing is hurt, tell the truth before the crack grows larger."
    elder.attrs["memory_item"] = {
        "metal": "tin music box",
        "glass": "glass bird",
        "cloth": "festival banner",
    }[relic.material]

    world.facts.update(
        params=params,
        relic_cfg=relic,
        damage_cfg=damage,
        helper_cfg=helper,
        fix_cfg=fix,
        hero=hero,
        elder=elder,
        helper=helper_ent,
        relic=relic_ent,
        kingdom=kingdom,
        outcome=outcome_of(params),
        flashback_happened=False,
    )

    introduce(world, hero, elder, relic)
    set_out(world, hero, relic)

    world.para()
    accident(world, hero, relic_ent, relic, damage)

    world.para()
    flashback(world, hero, elder, relic)
    choose_truth(world, hero)
    seek_helper(world, hero, helper_ent, helper)

    world.para()
    mend(world, hero, helper_ent, relic_ent, relic, damage, fix, helper)
    ending(world, hero, elder, relic_ent, relic)

    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
RELICS = {
    "moon_bell": Relic(
        id="moon_bell",
        label="moon bell",
        phrase="the old moon bell wrapped in blue velvet",
        material="metal",
        place="the hilltop arch",
        purpose="call every cottage window to glow",
        shine_word="silver voice",
        fragility=2,
        tags={"bell", "festival"},
    ),
    "star_mirror": Relic(
        id="star_mirror",
        label="star mirror",
        phrase="the star mirror in its willow frame",
        material="glass",
        place="the dew court",
        purpose="catch the first moonbeam and scatter it like milk-white stars",
        shine_word="clear face",
        fragility=3,
        tags={"mirror", "festival"},
    ),
    "dawn_banner": Relic(
        id="dawn_banner",
        label="dawn banner",
        phrase="the dawn banner folded in a rosewood chest",
        material="cloth",
        place="the castle bridge",
        purpose="wake the swallows and flutter over the feast",
        shine_word="golden hem",
        fragility=1,
        tags={"banner", "festival"},
    ),
}

DAMAGES = {
    "chip": Damage(
        id="chip",
        label="chip",
        verb_past="chipped",
        sign="a little piece missing from the edge",
        severity=1,
        allowed_materials={"metal", "glass"},
        tags={"break"},
    ),
    "crack": Damage(
        id="crack",
        label="crack",
        verb_past="cracked",
        sign="a thin line running across it",
        severity=2,
        allowed_materials={"glass", "metal"},
        tags={"break"},
    ),
    "tear": Damage(
        id="tear",
        label="tear",
        verb_past="tore",
        sign="a long rip through the weave",
        severity=1,
        allowed_materials={"cloth"},
        tags={"tear"},
    ),
}

HELPERS = {
    "bellsmith": Helper(
        id="bellsmith",
        label="the bellsmith",
        title="Bellsmith Rowan",
        place="the ember shop beside the well",
        crafts={"metal"},
        bonus=2,
        tags={"smith"},
    ),
    "glazier": Helper(
        id="glazier",
        label="the glazier",
        title="Glazier Fern",
        place="the crystal workshop under the lime tree",
        crafts={"glass"},
        bonus=2,
        tags={"glass"},
    ),
    "seamstress": Helper(
        id="seamstress",
        label="the seamstress",
        title="Seamstress Moth",
        place="the ribbon room over the bakery",
        crafts={"cloth"},
        bonus=2,
        tags={"sewing"},
    ),
    "royal_mender": Helper(
        id="royal_mender",
        label="the royal mender",
        title="Royal Mender Elowen",
        place="the round tower workroom",
        crafts={"metal", "glass", "cloth"},
        bonus=3,
        tags={"mending"},
    ),
}

FIXES = {
    "star_solder": Fix(
        id="star_solder",
        label="star solder",
        phrase="a pinch of star solder",
        materials={"metal"},
        strength=2,
        action="warmed the join until the silver edges kissed together",
        tags={"repair"},
    ),
    "moon_glue": Fix(
        id="moon_glue",
        label="moon glue",
        phrase="a drop of moon glue",
        materials={"glass"},
        strength=2,
        action="set the broken edge in place and held it while the pale glue cleared",
        tags={"repair"},
    ),
    "gold_thread": Fix(
        id="gold_thread",
        label="gold thread",
        phrase="a spool of gold thread",
        materials={"cloth"},
        strength=2,
        action="stitched the rip with tiny shining bites",
        tags={"repair"},
    ),
    "mender_dust": Fix(
        id="mender_dust",
        label="mender dust",
        phrase="a twist of mender dust",
        materials={"metal", "glass", "cloth"},
        strength=1,
        action="breathed the dust over the wound and smoothed the edges together",
        tags={"repair", "magic"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nella", "Poppy", "Tessa", "Ivy", "Wren"]
BOY_NAMES = ["Tobin", "Ari", "Milo", "Rowan", "Pip", "Finn", "Nico", "Soren"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bell": [(
        "What does a bell do?",
        "A bell makes a ringing sound when it is struck. People use bells to call others together or to mark an important time."
    )],
    "mirror": [(
        "What does a mirror do?",
        "A mirror reflects light and shows an image back to you. A shiny mirror can make a room look brighter too."
    )],
    "banner": [(
        "What is a banner?",
        "A banner is a long piece of cloth that can hang or wave in the air. People use banners to decorate a special place."
    )],
    "smith": [(
        "What does a smith do?",
        "A smith works with hot metal and tools to shape or mend metal things. It takes careful hands and patience."
    )],
    "glass": [(
        "Why can glass crack?",
        "Glass is hard but brittle, so a bump can send a thin crack through it. That is why people carry glass carefully."
    )],
    "sewing": [(
        "What does a seamstress do?",
        "A seamstress sews cloth so it can be made or mended. Strong stitches help torn fabric hold together again."
    )],
    "mending": [(
        "What does it mean to mend something?",
        "To mend something means to repair it after it is torn, cracked, or broken. Mending helps a useful or loved thing last longer."
    )],
    "festival": [(
        "What is a feast or festival?",
        "A feast or festival is a special time when people gather to celebrate together. They may sing, eat, and decorate the place."
    )],
    "truth": [(
        "Why is it good to tell the truth after a mistake?",
        "Telling the truth helps other people understand what happened and help fix it. Hiding a mistake often makes the problem harder."
    )],
}
KNOWLEDGE_ORDER = ["festival", "bell", "mirror", "banner", "smith", "glass", "sewing", "mending", "truth"]


def generation_prompts(world: World) -> list[str]:
    relic = world.facts["relic_cfg"]
    damage = world.facts["damage_cfg"]
    helper = world.facts["helper_cfg"]
    hero = world.facts["hero"]
    return [
        (
            f'Write a short fairy tale for a 3-to-5-year-old that includes the words '
            f'"millenium" and "chunk", and uses a flashback when a child makes a mistake.'
        ),
        (
            f"Tell a gentle fairy-tale story where {hero.id} damages a precious {relic.label}, "
            f"remembers an elder's lesson in a flashback, and goes to {helper.title} for help."
        ),
        (
            f"Write a story about a {damage.label} in a feast treasure, where the turning point "
            f"is honesty instead of hiding."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    relic = world.facts["relic_cfg"]
    damage = world.facts["damage_cfg"]
    helper = world.facts["helper_cfg"]
    fix = world.facts["fix_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {elder.label_word} who trusted "
            f"{hero.pronoun('object')} with {relic.phrase}. The story also includes {helper.title}, who helps mend it."
        ),
        (
            f"Why was the {relic.label} important?",
            f"It was important because it belonged at {relic.place} for the feast. The whole celebration depended on its "
            f"{relic.shine_word} to {relic.purpose}."
        ),
        (
            f"What happened to the {relic.label}?",
            f"It was damaged on the way to the feast. {hero.id} stumbled, and the treasure was left with {damage.sign}."
        ),
    ]
    if world.facts.get("flashback_happened"):
        qa.append((
            f"What did {hero.id} remember in the flashback?",
            f"{hero.pronoun().capitalize()} remembered {hero.pronoun('possessive')} {elder.label_word}'s lesson about telling the truth "
            f"when something precious is hurt. That memory gave {hero.pronoun('object')} courage to ask for help instead of hiding."
        ))
    qa.append((
        f"Why did {hero.id} go to {helper.title}?",
        f"{hero.id} went there because the relic was damaged and the feast was at risk. {helper.title} had the right craft for "
        f"{relic.material}, so asking for help was the sensible way to mend it."
    ))
    if outcome == "bright":
        qa.append((
            "How did the story end?",
            f"The relic was repaired so well that it shone brightly at the feast. The ending proves that honesty and quick help "
            f"saved the celebration."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"The relic was mended in time, though a bright seam still showed. That gentle mark mattered because it showed the truth "
            f"had been faced instead of hidden."
        ))
    qa.append((
        f"What lesson did {hero.id} learn?",
        f"{hero.id} learned to tell the truth quickly after a mistake. That choice brought wise help, and wise help turned worry into relief."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"festival", "truth", "mending"}
    relic = world.facts["relic_cfg"]
    helper = world.facts["helper_cfg"]
    tags |= set(relic.tags)
    tags |= set(helper.tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
damage_fits(R,D) :- relic_material(R,M), damage_material(D,M).
fix_fits(R,Fx)   :- relic_material(R,M), fix_material(Fx,M).
helper_fits(H,R) :- helper_skill(H,M), relic_material(R,M).

repair_power(H,Fx,P) :- helper_bonus(H,B), fix_strength(Fx,S), P = B + S.
repair_need(R,D,N)   :- relic_fragility(R,F), damage_severity(D,S), N = F + S.

can_mend(R,D,H,Fx) :- damage_fits(R,D), fix_fits(R,Fx), helper_fits(H,R),
                      repair_power(H,Fx,P), damage_severity(D,S), P >= S + 1.

valid(R,D,H,Fx) :- relic(R), damage(D), helper(H), fix(Fx), can_mend(R,D,H,Fx).

outcome(bright) :- chosen_relic(R), chosen_damage(D), chosen_helper(H), chosen_fix(Fx),
                   valid(R,D,H,Fx), repair_power(H,Fx,P), repair_need(R,D,N), P >= N.
outcome(mended) :- chosen_relic(R), chosen_damage(D), chosen_helper(H), chosen_fix(Fx),
                   valid(R,D,H,Fx), not outcome(bright).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for relic_id, relic in RELICS.items():
        lines.append(asp.fact("relic", relic_id))
        lines.append(asp.fact("relic_material", relic_id, relic.material))
        lines.append(asp.fact("relic_fragility", relic_id, relic.fragility))
    for damage_id, damage in DAMAGES.items():
        lines.append(asp.fact("damage", damage_id))
        lines.append(asp.fact("damage_severity", damage_id, damage.severity))
        for material in sorted(damage.allowed_materials):
            lines.append(asp.fact("damage_material", damage_id, material))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_bonus", helper_id, helper.bonus))
        for craft in sorted(helper.crafts):
            lines.append(asp.fact("helper_skill", helper_id, craft))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_strength", fix_id, fix.strength))
        for material in sorted(fix.materials):
            lines.append(asp.fact("fix_material", fix_id, material))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_relic", params.relic),
        asp.fact("chosen_damage", params.damage),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        relic="moon_bell",
        damage="chip",
        helper="bellsmith",
        fix="star_solder",
        hero_name="Lina",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        relic="star_mirror",
        damage="chip",
        helper="glazier",
        fix="moon_glue",
        hero_name="Tobin",
        hero_gender="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        relic="dawn_banner",
        damage="tear",
        helper="seamstress",
        fix="gold_thread",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="fairy_godmother",
    ),
    StoryParams(
        relic="star_mirror",
        damage="crack",
        helper="royal_mender",
        fix="mender_dust",
        hero_name="Pip",
        hero_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        relic="moon_bell",
        damage="crack",
        helper="royal_mender",
        fix="mender_dust",
        hero_name="Elsie",
        hero_gender="girl",
        elder_type="grandfather",
    ),
]


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a feast relic is damaged, a flashback guides honesty, and wise help mends it."
    )
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--damage", choices=sorted(DAMAGES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "fairy_godmother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible repair combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a generation smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    requested_relic = args.relic
    requested_damage = args.damage
    requested_helper = args.helper
    requested_fix = args.fix

    if requested_relic and requested_damage and requested_helper and requested_fix:
        relic = RELICS[requested_relic]
        damage = DAMAGES[requested_damage]
        helper = HELPERS[requested_helper]
        fix = FIXES[requested_fix]
        if not can_mend(relic, damage, helper, fix):
            raise StoryError(explain_rejection(relic, damage, helper, fix))

    combos = [
        combo for combo in valid_combos()
        if (requested_relic is None or combo[0] == requested_relic)
        and (requested_damage is None or combo[1] == requested_damage)
        and (requested_helper is None or combo[2] == requested_helper)
        and (requested_fix is None or combo[3] == requested_fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    relic_id, damage_id, helper_id, fix_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "fairy_godmother"])

    return StoryParams(
        relic=relic_id,
        damage=damage_id,
        helper=helper_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            asp_res = asp_outcome(params)
            py_res = outcome_of(params)
            if asp_res != py_res:
                bad += 1
        except Exception:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        _ = smoke.to_json()
        _ = format_qa(smoke)
        with redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=False, header="")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (relic, damage, helper, fix) combos:\n")
        for relic, damage, helper, fix in combos:
            params = StoryParams(
                relic=relic,
                damage=damage,
                helper=helper,
                fix=fix,
                hero_name="Lina",
                hero_gender="girl",
                elder_type="grandmother",
            )
            print(f"  {relic:12} {damage:6} {helper:12} {fix:12} [{outcome_of(params)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
                f"### {p.hero_name}: {p.relic} / {p.damage} / {p.helper} / {p.fix} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
