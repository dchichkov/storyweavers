#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/seventy_swallow_market_sharing_conflict_lesson_learned.py
====================================================================================

A small story world about a child in a dusk market, a hungry ghost, a quarrel over
sharing, and the lesson that a fair gift can calm fear.

Seed domain
-----------
- must include the words "seventy" and "swallow"
- setting: market
- features: Sharing, Conflict, Lesson Learned
- style: Ghost Story

This world turns that seed into a classical simulation: a child carries market food,
a hungry spirit appears, an adult guide explains the custom, and the ending depends
on whether the offered share is suitable and given soon enough.

Run it
------
    python storyworlds/worlds/gpt-5.4/seventy_swallow_market_sharing_conflict_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/seventy_swallow_market_sharing_conflict_lesson_learned.py --treat plum_bun --spirit child_ghost
    python storyworlds/worlds/gpt-5.4/seventy_swallow_market_sharing_conflict_lesson_learned.py --treat fish_skewer --spirit child_ghost
    python storyworlds/worlds/gpt-5.4/seventy_swallow_market_sharing_conflict_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4/seventy_swallow_market_sharing_conflict_lesson_learned.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/seventy_swallow_market_sharing_conflict_lesson_learned.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "auntie",
            "grandpa": "grandpa",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    tray_phrase: str
    ask_word: str
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
class Spirit:
    id: str
    label: str
    phrase: str
    ask: str
    accepted_tags: set[str] = field(default_factory=set)
    need: int = 1
    shape: str = ""
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
class Guide:
    id: str
    type: str
    label: str
    entrance: str
    lesson: str
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
class SharePlan:
    id: str
    count: int
    phrase: str
    hand_phrase: str
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


def _r_hungry_chill(world: World) -> list[str]:
    spirit = world.get("spirit")
    child = world.get("child")
    market = world.get("market")
    if spirit.meters["hunger"] < THRESHOLD:
        return []
    if world.facts.get("shared_enough"):
        return []
    sig = ("hungry_chill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    market.meters["cold"] += 1
    child.memes["fear"] += 1
    return ["__chill__"]


def _r_clutch_conflict(world: World) -> list[str]:
    spirit = world.get("spirit")
    child = world.get("child")
    market = world.get("market")
    if spirit.meters["hunger"] < THRESHOLD or child.memes["greed"] < THRESHOLD:
        return []
    sig = ("clutch_conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    market.meters["noise"] += 1
    child.memes["conflict"] += 1
    spirit.memes["offended"] += 1
    return ["__conflict__"]


def _r_share_fit(world: World) -> list[str]:
    spirit = world.get("spirit")
    market = world.get("market")
    child = world.get("child")
    packet = world.get("packet")
    if not world.facts.get("shared_fit"):
        return []
    if not world.facts.get("shared_enough"):
        return []
    sig = ("share_fit",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spirit.meters["hunger"] = 0.0
    spirit.meters["rest"] += 1
    market.meters["cold"] = 0.0
    market.meters["warmth"] += 1
    child.memes["kindness"] += 1
    child.memes["fear"] = 0.0
    packet.meters["shared"] += float(world.facts.get("share_count", 0))
    return ["__rest__"]


def _r_delay_spill(world: World) -> list[str]:
    child = world.get("child")
    packet = world.get("packet")
    market = world.get("market")
    if world.facts.get("delay", 0) < 2:
        return []
    if child.memes["conflict"] < THRESHOLD:
        return []
    sig = ("delay_spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    packet.meters["spilled"] += 1
    market.meters["mess"] += 1
    child.memes["regret"] += 1
    return ["__spill__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="hungry_chill", tag="mood", apply=_r_hungry_chill),
    Rule(name="clutch_conflict", tag="social", apply=_r_clutch_conflict),
    Rule(name="share_fit", tag="resolution", apply=_r_share_fit),
    Rule(name="delay_spill", tag="physical", apply=_r_delay_spill),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def offer_works(treat: Treat, spirit: Spirit, share: SharePlan) -> bool:
    return bool(treat.tags & spirit.accepted_tags) and share.count >= spirit.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for treat_id, treat in TREATS.items():
        for spirit_id, spirit in SPIRITS.items():
            for share_id, share in SHARE_PLANS.items():
                if offer_works(treat, spirit, share):
                    combos.append((treat_id, spirit_id, share_id))
    return combos


def explain_rejection(treat: Treat, spirit: Spirit, share: SharePlan) -> str:
    if not (treat.tags & spirit.accepted_tags):
        wanted = ", ".join(sorted(spirit.accepted_tags))
        has = ", ".join(sorted(treat.tags))
        return (
            f"(No story: {spirit.label} would not accept {treat.label}. "
            f"This spirit settles only for offerings tagged {wanted}, but "
            f"{treat.label} is tagged {has}.)"
        )
    if share.count < spirit.need:
        return (
            f"(No story: {share.phrase} is too small for {spirit.label}. "
            f"That spirit needs at least {spirit.need} piece(s) to feel truly shared with.)"
        )
    return "(No story: this offering would not calm the spirit.)"


def outcome_of(params: "StoryParams") -> str:
    treat = TREATS[params.treat]
    spirit = SPIRITS[params.spirit]
    share = SHARE_PLANS[params.share]
    if not offer_works(treat, spirit, share):
        return "unfit"
    return "uneasy" if params.delay >= 2 else "peace"


def predict_market(world: World, treat: Treat, spirit: Spirit, share: SharePlan, delay: int) -> dict:
    sim = world.copy()
    sim.facts["shared_fit"] = bool(treat.tags & spirit.accepted_tags)
    sim.facts["shared_enough"] = share.count >= spirit.need
    sim.facts["share_count"] = share.count
    sim.facts["delay"] = delay
    sim.get("child").memes["greed"] += 1
    propagate(sim, narrate=False)
    if delay >= 2:
        sim.get("child").memes["conflict"] += 1
        propagate(sim, narrate=False)
    return {
        "cold": sim.get("market").meters["cold"],
        "spill": sim.get("packet").meters["spilled"],
        "peace": sim.get("spirit").meters["rest"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, guardian: Entity, treat: Treat) -> None:
    world.say(
        f"At the evening market, red lanterns swayed above the stalls, and a swallow "
        f"cut one dark loop across the smoky sky."
    )
    world.say(
        f"On Auntie Fen's table lay seventy {treat.tray_phrase}, shining in the lamplight "
        f"like little moons with steam still rising from them."
    )
    world.say(
        f"{child.id} had come with {child.pronoun('possessive')} {guardian.label_word} "
        f"to buy {treat.phrase} for the walk home."
    )


def carrying_home(world: World, child: Entity, treat: Treat) -> None:
    child.memes["pride"] += 1
    packet = world.get("packet")
    packet.meters["whole"] = 1.0
    world.say(
        f"The warm paper packet rested in {child.pronoun('possessive')} hands, and "
        f"{child.pronoun()} held it carefully, pleased to be trusted with something so good."
    )


def haunting_appearance(world: World, spirit: Spirit) -> None:
    world.get("spirit").meters["hunger"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Near the old well between the fruit stall and the tea stall, a pale shape "
        f"slid out of the dusk. It was {spirit.phrase}."
    )
    world.say(f'"{spirit.ask}" it whispered.')
    if world.get("market").meters["cold"] >= THRESHOLD:
        world.say(
            "At once the market seemed to breathe in. The lantern light thinned, "
            "and the warm smells of soup and sugar turned strangely cold."
        )


def clutch_and_quarrel(world: World, child: Entity, spirit: Spirit, treat: Treat) -> None:
    child.memes["greed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} hugged the packet to {child.pronoun('possessive')} chest. "
        f'"No," {child.pronoun()} said. "These are ours."'
    )
    if world.get("child").memes["conflict"] >= THRESHOLD:
        world.say(
            f"The ghost's eyes brightened like wet pebbles. A wind ran under the stalls, "
            f"rattling bowls and tugging at the paper around the {treat.ask_word}."
        )
        world.say(
            f'"I asked for a share," said the spirit, and the words made the shadows shiver.'
        )


def guide_steps_in(world: World, guide: Entity, spirit: Spirit, treat: Treat, share: SharePlan) -> None:
    pred = predict_market(world, treat, spirit, share, world.facts["delay"])
    world.facts["predicted_cold"] = pred["cold"]
    world.facts["predicted_spill"] = pred["spill"]
    guide.memes["calm"] += 1
    world.say(
        f"Then {guide.id} {guide.attrs['entrance']} and laid one steady hand on the counter."
    )
    world.say(
        f'"Hush now," {guide.pronoun()} said. "{guide.attrs["lesson"]}"'
    )


def choice_to_share(world: World, child: Entity, treat: Treat, share: SharePlan, spirit: Spirit) -> None:
    world.say(
        f"{child.id} looked at the packet, then at {spirit.label}. The market was still, "
        f"as if every hanging lantern were waiting for the choice."
    )
    if world.facts["delay"] >= 2:
        world.say(
            f"For a few frightened heartbeats, {child.id} only clutched the food harder. "
            f"The quarrel had already lasted too long."
        )
        world.get("child").memes["conflict"] += 1
        propagate(world, narrate=False)
    world.say(
        f"At last, {child.pronoun()} opened the packet and held out {share.hand_phrase}."
    )
    world.facts["shared_fit"] = bool(treat.tags & spirit.accepted_tags)
    world.facts["shared_enough"] = share.count >= spirit.need
    world.facts["share_count"] = share.count
    propagate(world, narrate=False)


def peaceful_resolution(world: World, child: Entity, spirit: Spirit, guide: Entity, treat: Treat) -> None:
    world.say(
        f"{spirit.label.capitalize()} took the offering with both thin hands. The {treat.ask_word} "
        f"did not vanish all at once; it faded like steam on winter glass."
    )
    world.say(
        "The cold left the market. Lanterns shone round again, and people who had been peeking "
        "from behind baskets let out the breaths they were holding."
    )
    world.say(
        f'"A fair share breaks a hungry quarrel," {guide.id} said softly. "{guide.attrs["closing"]}"'
    )
    world.say(
        f"When {child.id} and {child.pronoun('possessive')} family walked home, {child.pronoun()} "
        f"carried the smaller packet with a lighter heart."
    )


def uneasy_resolution(world: World, child: Entity, spirit: Spirit, guide: Entity, treat: Treat) -> None:
    spilled = world.get("packet").meters["spilled"] >= THRESHOLD
    if spilled:
        world.say(
            f"Before the spirit took the offering, the wind snapped the paper once, and "
            f"two of the {treat.ask_word} dropped to the stones."
        )
    world.say(
        f"Still, when the share was finally given, {spirit.label} bowed and ate in a hush of mist."
    )
    world.say(
        f'The lanterns brightened, but {child.id} kept staring at the fallen food. '
        f'"I should have shared sooner," {child.pronoun()} whispered.'
    )
    world.say(
        f'{guide.id} nodded. "{guide.attrs["closing"]} Kindness given late can still help, '
        f'but late kindness often costs more."'
    )
    world.say(
        f"After that night, {child.id} never squeezed a blessing into a quarrel again."
    )
def tell(
    spirit_cfg: Spirit,
    guide_cfg: Guide,
    share_cfg: Share,
    child_name: str,
    child_type: ChildType,
    guardian_type: GuardianType,
    trait: Trait,
    delay: Delay,
    treat=None,
) -> World:
    world = World()
    world.facts["delay"] = delay
    world.facts["shared_fit"] = False
    world.facts["shared_enough"] = False
    world.facts["share_count"] = 0

    market = world.add(Entity(id="market", type="place", label="the market"))
    market.meters["cold"] = 0.0
    market.meters["warmth"] = 0.0
    market.meters["noise"] = 0.0
    market.meters["mess"] = 0.0

    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", traits=[trait]))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, role="guardian", label="the guardian"))
    guide = world.add(
        Entity(
            id=guide_cfg.label,
            kind="character",
            type=guide_cfg.type,
            role="guide",
            label=guide_cfg.label,
            attrs={"entrance": guide_cfg.entrance, "lesson": guide_cfg.lesson, "closing": guide_cfg.closing},
            tags=set(guide_cfg.tags),
        )
    )
    spirit = world.add(
        Entity(
            id="spirit",
            kind="character",
            type="ghost",
            role="spirit",
            label=spirit_cfg.label,
            attrs={"shape": spirit_cfg.shape},
            tags=set(spirit_cfg.tags),
        )
    )
    packet = world.add(
        Entity(
            id="packet",
            type="packet",
            label=treat.label,
            attrs={"treat": treat.id},
            tags=set(treat.tags),
        )
    )

    child.memes["fear"] = 0.0
    child.memes["greed"] = 0.0
    child.memes["conflict"] = 0.0
    child.memes["kindness"] = 0.0
    child.memes["regret"] = 0.0
    spirit.meters["hunger"] = 0.0
    spirit.meters["rest"] = 0.0
    packet.meters["spilled"] = 0.0
    packet.meters["shared"] = 0.0

    opening(world, child, guardian, treat)
    carrying_home(world, child, treat)

    world.para()
    haunting_appearance(world, spirit_cfg)
    clutch_and_quarrel(world, child, spirit, treat)

    world.para()
    guide_steps_in(world, guide, spirit_cfg, treat, share_cfg)
    choice_to_share(world, child, treat, share_cfg, spirit_cfg)

    world.para()
    if outcome_of(
        StoryParams(
            treat=treat.id,
            spirit=spirit_cfg.id,
            guide=guide_cfg.id,
            share=share_cfg.id,
            child=child_name,
            gender=child_type,
            guardian=guardian_type,
            trait=trait,
            delay=delay,
            seed=None,
        )
    ) == "peace":
        peaceful_resolution(world, child, spirit, guide, treat)
        outcome = "peace"
    else:
        uneasy_resolution(world, child, spirit, guide, treat)
        outcome = "uneasy"

    world.facts.update(
        child=child,
        guardian=guardian,
        guide=guide,
        spirit=spirit,
        treat_cfg=treat,
        spirit_cfg=spirit_cfg,
        guide_cfg=guide_cfg,
        share_cfg=share_cfg,
        outcome=outcome,
        spilled=packet.meters["spilled"] >= THRESHOLD,
        shared_count=share_cfg.count,
        lesson=guide_cfg.lesson,
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


TREATS = {
    "plum_bun": Treat(
        id="plum_bun",
        label="plum bun",
        phrase="a packet of warm plum buns",
        tray_phrase="plum buns",
        ask_word="buns",
        tags={"sweet", "warm"},
    ),
    "sesame_cake": Treat(
        id="sesame_cake",
        label="sesame cake",
        phrase="a packet of sesame cakes",
        tray_phrase="sesame cakes",
        ask_word="cakes",
        tags={"sweet", "crumbly"},
    ),
    "pear_slice": Treat(
        id="pear_slice",
        label="candied pear slice",
        phrase="a paper fold of candied pear slices",
        tray_phrase="candied pear slices",
        ask_word="pear slices",
        tags={"sweet", "cool"},
    ),
    "fish_skewer": Treat(
        id="fish_skewer",
        label="fish skewer",
        phrase="a packet of grilled fish skewers",
        tray_phrase="fish skewers",
        ask_word="skewers",
        tags={"savory", "warm"},
    ),
}

SPIRITS = {
    "child_ghost": Spirit(
        id="child_ghost",
        label="the hungry child ghost",
        phrase="a little ghost in a faded blue coat, barefoot and shivering",
        ask="Please... just one sweet bite. Will you share?",
        accepted_tags={"sweet", "warm"},
        need=1,
        shape="small and thin as moon-smoke",
        tags={"ghost_child", "sharing"},
    ),
    "old_vendor": Spirit(
        id="old_vendor",
        label="the old vendor spirit",
        phrase="an old market ghost with sleeves like torn fog and a voice like paper",
        ask="The stall is closed, little one, but old hunger still walks. Have you a warm share?",
        accepted_tags={"warm"},
        need=2,
        shape="bent over an invisible tray",
        tags={"ghost_vendor", "sharing"},
    ),
    "swallow_shadow": Spirit(
        id="swallow_shadow",
        label="the swallow-shadow spirit",
        phrase="a bird-shaped shadow that kept becoming a person and then a bird again",
        ask="Three sweet crumbs for a swallow that lost its nest. Will you share?",
        accepted_tags={"sweet", "crumbly"},
        need=3,
        shape="wings in the lantern smoke",
        tags={"swallow", "sharing"},
    ),
}

GUIDES = {
    "lantern_aunt": Guide(
        id="lantern_aunt",
        type="aunt",
        label="Lantern Auntie",
        entrance="stepped out from the lantern stall, her sleeves smelling faintly of cedar smoke",
        lesson="When the hungry dead ask politely at market, we do not mock them and we do not clutch. We share a fair little part, so the road stays peaceful for everyone",
        closing="A gift does not make your supper smaller in the heart. It makes the road home wider",
        tags={"adult_help", "lantern"},
    ),
    "tea_grandpa": Guide(
        id="tea_grandpa",
        type="grandpa",
        label="Tea Grandpa",
        entrance="lifted the kettle lid at the tea stall and looked over through the steam",
        lesson="Old markets remember every hand that gave and every hand that snatched. A fair share cools angry hunger before it grows teeth",
        closing="If you keep every crumb for yourself, even good food can turn heavy",
        tags={"adult_help", "tea"},
    ),
    "noodle_mother": Guide(
        id="noodle_mother",
        type="mother",
        label="Noodle Mother",
        entrance="wiped her hands on her apron and came from the noodle cart with calm eyes",
        lesson="A market feeds many people, living and dead. We keep peace by sharing enough, not by fighting over every bite",
        closing="What is shared with kindness comes back as safety",
        tags={"adult_help", "noodles"},
    ),
}

SHARE_PLANS = {
    "one": SharePlan(
        id="one",
        count=1,
        phrase="one piece",
        hand_phrase="one piece in both hands",
        tags={"small_share"},
    ),
    "two": SharePlan(
        id="two",
        count=2,
        phrase="two pieces",
        hand_phrase="two pieces on the open paper",
        tags={"fair_share"},
    ),
    "three": SharePlan(
        id="three",
        count=3,
        phrase="three pieces",
        hand_phrase="three pieces together, carefully counted",
        tags={"fair_share"},
    ),
}

GIRL_NAMES = ["Mei", "Lian", "Yun", "Nora", "Tessa", "Asha"]
BOY_NAMES = ["Bo", "Tao", "Jun", "Eli", "Milo", "Ren"]
TRAITS = ["careful", "proud", "quick", "quiet", "curious"]


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with a spooky visitor from the past or from somewhere unseen. It can feel chilly and mysterious without being cruel."
        )
    ],
    "market": [
        (
            "What is a market?",
            "A market is a place where many people gather to buy and sell food or other things. It is usually full of voices, smells, and little stalls."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else have part of what you have. It shows care, fairness, and room in your heart for another person."
        )
    ],
    "swallow": [
        (
            "What is a swallow?",
            "A swallow is a small bird with pointed wings that can dart quickly through the air. People often notice swallows because they fly in fast, graceful loops."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light so people can see in the dark. In stories, lantern light often makes a place feel warm and safe."
        )
    ],
    "lesson": [
        (
            "Why is it wise to stop a quarrel early?",
            "Stopping a quarrel early keeps hurt feelings from growing bigger. A calm choice made soon can prevent a small problem from becoming a messy one."
        )
    ],
}
KNOWLEDGE_ORDER = ["market", "ghost", "sharing", "swallow", "lantern", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    spirit = f["spirit_cfg"]
    treat = f["treat_cfg"]
    outcome = f["outcome"]
    if outcome == "peace":
        return [
            f'Write a gentle ghost story for a 3-to-5-year-old set in a market that includes the words "seventy" and "swallow".',
            f"Tell a story where {child.id} meets {spirit.label} beside a market well, learns to share {treat.label}, and makes the walk home peaceful again.",
            f"Write a child-facing spooky story about sharing, a small conflict, and a lesson learned from a market ghost."
        ]
    return [
        f'Write a soft ghost story for a 3-to-5-year-old set in a market that includes the words "seventy" and "swallow".',
        f"Tell a story where {child.id} quarrels with {spirit.label} over {treat.label}, then learns the lesson a little late after some food is lost.",
        f"Write a spooky-but-kind story about sharing at a market, where a delayed good choice still teaches an important lesson."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    spirit_cfg = f["spirit_cfg"]
    treat = f["treat_cfg"]
    share = f["share_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Where did the story happen?",
            "It happened at the evening market, with lanterns over the stalls and an old well between them. The market setting matters because it is a place where many people share food and space."
        ),
        (
            f"What was {child.id} carrying?",
            f"{child.id} was carrying {treat.phrase}. The packet felt important, which is part of why {child.pronoun()} clutched it when the ghost asked for some."
        ),
        (
            "What made the story feel spooky?",
            f"A pale spirit came out near the well, the air turned cold, and the lantern light thinned. Those changes showed that the ghost's hunger was troubling the whole market."
        ),
        (
            f"Why did {child.id} and the ghost have a conflict?",
            f"The ghost asked for a fair share of the food, but {child.id} hugged the packet close and said no. That refusal turned fear into a quarrel and made the market feel colder."
        ),
        (
            f"What lesson did {guide.id} teach?",
            f'{guide.id} taught that a fair share can calm hungry anger and keep the road peaceful. The lesson was not only about food, but about refusing to let fear make every choice.'
        ),
    ]
    if f["outcome"] == "peace":
        qa.append(
            (
                f"How was the problem solved?",
                f"{child.id} opened the packet and shared {share.phrase}, which was the right kind of offering for {spirit_cfg.label}. Because the gift was fair and given in time, the ghost rested and the cold left the market."
            )
        )
        qa.append(
            (
                f"How did {child.id} change by the end?",
                f"{child.id} began by clutching the food in fear, but ended the story carrying less food and more peace. The ending shows that sharing made {child.pronoun('possessive')} heart lighter, not emptier."
            )
        )
    else:
        qa.append(
            (
                "Did sharing still help, even though it came late?",
                f"Yes. The share still calmed the spirit, but the delay let the quarrel grow long enough for food to be lost first. That is why the lesson became sharper: kindness given late can still mend trouble, but it cannot always undo the cost."
            )
        )
        qa.append(
            (
                f"What did {child.id} learn from the spilled food?",
                f"{child.id} learned that squeezing every bite into a fight only makes the loss feel larger. Sharing sooner would have saved both the peace of the market and the fallen food."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"market", "ghost", "sharing", "lesson"}
    spirit = world.facts["spirit_cfg"]
    guide = world.facts["guide_cfg"]
    if "swallow" in spirit.tags:
        tags.add("swallow")
    if "lantern" in guide.tags:
        tags.add("lantern")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:14} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    treat: str
    spirit: str
    guide: str
    share: str
    child: str
    gender: str
    guardian: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        treat="plum_bun",
        spirit="child_ghost",
        guide="lantern_aunt",
        share="one",
        child="Mei",
        gender="girl",
        guardian="mother",
        trait="careful",
        delay=0,
        seed=None,
    ),
    StoryParams(
        treat="sesame_cake",
        spirit="swallow_shadow",
        guide="tea_grandpa",
        share="three",
        child="Bo",
        gender="boy",
        guardian="father",
        trait="quick",
        delay=0,
        seed=None,
    ),
    StoryParams(
        treat="fish_skewer",
        spirit="old_vendor",
        guide="noodle_mother",
        share="two",
        child="Jun",
        gender="boy",
        guardian="mother",
        trait="proud",
        delay=1,
        seed=None,
    ),
    StoryParams(
        treat="plum_bun",
        spirit="old_vendor",
        guide="tea_grandpa",
        share="two",
        child="Lian",
        gender="girl",
        guardian="father",
        trait="quiet",
        delay=2,
        seed=None,
    ),
]


ASP_RULES = r"""
offer_fit(T,S) :- treat(T), spirit(S), accepted(S,Tag), has_tag(T,Tag).
offer_enough(S,Sh) :- spirit(S), share(Sh), need(S,N), share_count(Sh,C), C >= N.
valid(T,S,Sh) :- offer_fit(T,S), offer_enough(S,Sh).

peace :- chosen_treat(T), chosen_spirit(S), chosen_share(Sh), valid(T,S,Sh), delay(D), D < 2.
uneasy :- chosen_treat(T), chosen_spirit(S), chosen_share(Sh), valid(T,S,Sh), delay(D), D >= 2.
outcome(peace) :- peace.
outcome(uneasy) :- uneasy.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        for tag in sorted(treat.tags):
            lines.append(asp.fact("has_tag", treat_id, tag))
    for spirit_id, spirit in SPIRITS.items():
        lines.append(asp.fact("spirit", spirit_id))
        lines.append(asp.fact("need", spirit_id, spirit.need))
        for tag in sorted(spirit.accepted_tags):
            lines.append(asp.fact("accepted", spirit_id, tag))
    for share_id, share in SHARE_PLANS.items():
        lines.append(asp.fact("share", share_id))
        lines.append(asp.fact("share_count", share_id, share.count))
    for guide_id in GUIDES:
        lines.append(asp.fact("guide", guide_id))
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
            asp.fact("chosen_treat", params.treat),
            asp.fact("chosen_spirit", params.spirit),
            asp.fact("chosen_share", params.share),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=True, qa=True, header="### smoke")
    _ = sample.to_json()


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke-tested generate()/emit()/json.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a market ghost, a quarrel over sharing, and a lesson learned."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--share", choices=SHARE_PLANS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("--child")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible offering set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.spirit and args.share:
        treat = TREATS[args.treat]
        spirit = SPIRITS[args.spirit]
        share = SHARE_PLANS[args.share]
        if not offer_works(treat, spirit, share):
            raise StoryError(explain_rejection(treat, spirit, share))

    combos = [
        combo
        for combo in valid_combos()
        if (args.treat is None or combo[0] == args.treat)
        and (args.spirit is None or combo[1] == args.spirit)
        and (args.share is None or combo[2] == args.share)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treat_id, spirit_id, share_id = rng.choice(sorted(combos))
    guide_id = args.guide or rng.choice(sorted(GUIDES))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        treat=treat_id,
        spirit=spirit_id,
        guide=guide_id,
        share=share_id,
        child=child,
        gender=gender,
        guardian=guardian,
        trait=trait,
        delay=delay,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.spirit not in SPIRITS:
        raise StoryError(f"(Unknown spirit: {params.spirit})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.share not in SHARE_PLANS:
        raise StoryError(f"(Unknown share plan: {params.share})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.guardian not in {"mother", "father"}:
        raise StoryError(f"(Unknown guardian: {params.guardian})")
    if params.delay not in {0, 1, 2}:
        raise StoryError(f"(Invalid delay: {params.delay})")

    treat = TREATS[params.treat]
    spirit = SPIRITS[params.spirit]
    share = SHARE_PLANS[params.share]
    if not offer_works(treat, spirit, share):
        raise StoryError(explain_rejection(treat, spirit, share))

    world = tell(
        treat=treat,
        spirit_cfg=spirit,
        guide_cfg=GUIDES[params.guide],
        share_cfg=share,
        child_name=params.child,
        child_type=params.gender,
        guardian_type=params.guardian,
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
        print(f"{len(combos)} compatible (treat, spirit, share) combos:\n")
        for treat_id, spirit_id, share_id in combos:
            print(f"  {treat_id:12} {spirit_id:15} {share_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.child}: {p.treat} for {p.spirit} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
