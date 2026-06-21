#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chomp_shopping_mall_reconciliation_fable.py
======================================================================

A standalone story world for a small fable-like tale set in a shopping mall.

Premise
-------
Two young animal friends visit the shopping mall. They plan to share a treat,
but one friend takes a greedy chomp before the sharing moment. The other friend
feels hurt. The story only becomes whole if the offender makes a fitting repair:
sometimes a careful apology and the best remaining piece are enough, and
sometimes only buying a whole new treat can mend the friendship.

This world models:
- typed entities with physical meters and emotional memes
- a simple forward-chaining rule layer
- a Python reasonableness gate plus an inline ASP twin
- three QA sets generated from the simulated world, not by parsing English

Run it
------
    python storyworlds/worlds/gpt-5.4/chomp_shopping_mall_reconciliation_fable.py
    python storyworlds/worlds/gpt-5.4/chomp_shopping_mall_reconciliation_fable.py --stall pretzel_cart --snack pretzel
    python storyworlds/worlds/gpt-5.4/chomp_shopping_mall_reconciliation_fable.py --repair apology_only --bite 2
    python storyworlds/worlds/gpt-5.4/chomp_shopping_mall_reconciliation_fable.py --all
    python storyworlds/worlds/gpt-5.4/chomp_shopping_mall_reconciliation_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/chomp_shopping_mall_reconciliation_fable.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "hen", "doe", "vixen"}
        male = {"boy", "father", "uncle", "buck", "fox", "bear"}
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
            "uncle": "uncle",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registry dataclasses
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
class Stall:
    id: str
    label: str
    smell: str
    affords: set[str] = field(default_factory=set)
    image: str = ""
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
class Snack:
    id: str
    label: str
    phrase: str
    share_name: str
    bite_name: str
    pieces: int
    split_kind: str
    crunch_line: str
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
class Repair:
    id: str
    sense: int
    power: int
    needs_coin: int = 0
    needs_remaining: int = 0
    text: str = ""
    qa_text: str = ""
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
class Pairing:
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    relation_word: str
    elder_word: str = ""


# ---------------------------------------------------------------------------
# World and rules
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


def _r_broken_promise(world: World) -> list[str]:
    snack = world.get("snack")
    hero = world.get("hero")
    friend = world.get("friend")
    if not world.facts.get("promised_share"):
        return []
    if snack.meters["bitten"] < THRESHOLD:
        return []
    sig = ("broken_promise",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    friend.memes["anger"] += 1
    hero.memes["guilt"] += 1
    return ["__hurt__"]


def _r_apology_softens(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if friend.memes["hurt"] < THRESHOLD or hero.memes["apology"] < THRESHOLD:
        return []
    sig = ("apology_softens",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["softened"] += 1
    return []


def _r_repair_restores_trust(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if friend.memes["softened"] < THRESHOLD:
        return []
    if hero.memes["repair"] < THRESHOLD:
        return []
    sig = ("repair_restores",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["trust"] += 1
    friend.memes["hurt"] = 0.0
    friend.memes["anger"] = 0.0
    hero.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="broken_promise", tag="social", apply=_r_broken_promise),
    Rule(name="apology_softens", tag="social", apply=_r_apology_softens),
    Rule(name="repair_restores_trust", tag="social", apply=_r_repair_restores_trust),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def sold_here(stall: Stall, snack: Snack) -> bool:
    return snack.id in stall.affords


def can_perform_repair(repair: Repair, snack: Snack, bite: int, coins: int) -> bool:
    remaining = snack.pieces - bite
    if coins < repair.needs_coin:
        return False
    if remaining < repair.needs_remaining:
        return False
    return True


def offense_severity(bite: int) -> int:
    return bite


def is_reconciled(repair: Repair, snack: Snack, bite: int, coins: int) -> bool:
    if not can_perform_repair(repair=repair, snack=snack, bite=bite, coins=coins):
        return False
    return repair.power >= offense_severity(bite)


def valid_combos() -> list[tuple[str, str, str, int, int]]:
    combos: list[tuple[str, str, str, int, int]] = []
    for stall_id, stall in STALLS.items():
        for snack_id, snack in SNACKS.items():
            if not sold_here(stall=stall, snack=snack):
                continue
            for repair_id, repair in REPAIRS.items():
                if repair.sense < SENSE_MIN:
                    continue
                for coins in (0, 1, 2):
                    for bite in (1, 2):
                        if bite > snack.pieces:
                            continue
                        if can_perform_repair(repair=repair, snack=snack, bite=bite, coins=coins):
                            combos.append((stall_id, snack_id, repair_id, coins, bite))
    return combos


def explain_sale(stall: Stall, snack: Snack) -> str:
    return (
        f"(No story: {stall.label} does not sell {snack.label}. "
        f"Pick a snack that belongs at that stall.)"
    )


def explain_repair(repair: Repair, snack: Snack, bite: int, coins: int) -> str:
    remaining = snack.pieces - bite
    if coins < repair.needs_coin:
        return (
            f"(No story: {repair.id} needs at least {repair.needs_coin} spare coin, "
            f"but only {coins} {'coin is' if coins == 1 else 'coins are'} available.)"
        )
    if remaining < repair.needs_remaining:
        return (
            f"(No story: after a bite of {bite}, only {remaining} piece"
            f"{'' if remaining == 1 else 's'} remain, and {repair.id} needs "
            f"{repair.needs_remaining} piece{'s' if repair.needs_remaining != 1 else ''} left.)"
        )
    return "(No story: that repair does not fit this snack and bite.)"


# ---------------------------------------------------------------------------
# Prediction helper
# ---------------------------------------------------------------------------
def predict_feelings(world: World, repair: Repair) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    friend = sim.get("friend")
    snack = sim.get("snack")
    hero.memes["apology"] += 1
    if repair.id == "offer_best_piece":
        if snack.meters["remaining"] >= repair.needs_remaining:
            hero.memes["repair"] += 1
    elif repair.id == "buy_replacement":
        if hero.attrs.get("coins", 0) >= repair.needs_coin:
            hero.memes["repair"] += 1
    elif repair.id == "carry_bags_and_apologize":
        hero.memes["repair"] += 1
    propagate(sim, narrate=False)
    return {
        "hurt": friend.memes["hurt"],
        "trust": friend.memes["trust"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def opening(world: World, stall: Stall, pairing: Pairing, guardian: Entity) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the bright shopping mall, where the escalator hummed and the fountain "
        f"threw silver drops into the air, {hero.id} and {friend.id} walked beside "
        f"{guardian.label_word}. They were small enough to look up at every shining sign "
        f"and wise enough, on most days, to hold paws when the crowd grew thick."
    )
    world.say(
        f"They stopped by {stall.label}, where {stall.smell} floated through the food court. "
        f"{stall.image}"
    )


def choose_treat(world: World, snack: Snack) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    snack_ent = world.get("snack")
    snack_ent.meters["whole"] = 1.0
    snack_ent.meters["remaining"] = float(snack.pieces)
    world.facts["promised_share"] = True
    world.say(
        f'Together they chose {snack.phrase}. "{snack.share_name.capitalize()} for both of us," '
        f"said {friend.id}, and {hero.id} nodded. A shared treat seemed small, but in a friendship "
        f"small promises are counted carefully."
    )


def tempt(world: World, snack: Snack) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["greed"] += 1
    world.say(
        f"Then the warm smell curled up again, and {hero.id}'s eyes followed the treat. "
        f"{friend.id} had turned for only a blink to watch coins shimmer in the fountain."
    )


def greedy_bite(world: World, snack: Snack, bite: int) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    snack_ent = world.get("snack")
    snack_ent.meters["bitten"] += 1
    snack_ent.meters["remaining"] = float(max(0, snack.pieces - bite))
    snack_ent.meters["lost_share"] = float(bite)
    world.facts["bite"] = bite
    propagate(world, narrate=False)
    bites = {
        1: f"one quick {snack.bite_name}",
        2: f"two hurried {snack.bite_name}s",
    }[bite]
    world.say(
        f"And then came the greedy moment: {hero.id} took {bites} -- chomp! {snack.crunch_line} "
        f"When {friend.id} turned back, the shared treat was no longer fair."
    )
    if friend.memes["hurt"] >= THRESHOLD:
        world.say(
            f'{friend.id} blinked and drew back. "You promised to wait," {friend.pronoun()} said. '
            f"Hurt is quiet at first, but it changes the whole air around a friend."
        )


def walk_apart(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["lonely"] += 1
    friend.memes["sadness"] += 1
    world.say(
        f"{friend.id} moved to the edge of the fountain and would not meet {hero.id}'s eyes. "
        f"The mall was still full of music and footsteps, yet for the two friends it suddenly felt large."
    )


def notice_and_learn(world: World, repair: Repair) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    pred = predict_feelings(world, repair=repair)
    world.facts["predicted_hurt_after_repair"] = pred["hurt"]
    world.facts["predicted_trust_after_repair"] = pred["trust"]
    world.say(
        f"{hero.id} saw {friend.id}'s face in the fountain water: smaller than a moment ago, and sadder. "
        f"In that wavering mirror, greed looked foolish."
    )
    world.say(
        f"{hero.pronoun().capitalize()} remembered that a bite can be swallowed in a second, "
        f"but friendship takes longer to build."
    )


def apologize(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} went softly to {friend.id}. "I was greedy, and I broke my promise," '
        f'{hero.pronoun()} said. "I am sorry."'
    )


def do_repair(world: World, repair: Repair, snack: Snack, guardian: Entity) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    snack_ent = world.get("snack")
    if repair.id == "offer_best_piece":
        hero.memes["repair"] += 1
        snack_ent.meters["given_back"] += 1
        world.say(
            f"Then {hero.id} turned the treat in {hero.pronoun('possessive')} paws and offered "
            f"the best unbitten {snack.split_kind} to {friend.id}. It was not magic, but it was the "
            f"fairest piece left."
        )
    elif repair.id == "buy_replacement":
        hero.attrs["coins"] = int(hero.attrs.get("coins", 0)) - repair.needs_coin
        hero.memes["repair"] += 1
        snack_ent.meters["replacement_bought"] += 1
        world.say(
            f"Then {hero.id} opened {hero.pronoun('possessive')} little purse and spent a spare coin "
            f"on a fresh {snack.label} for {friend.id}. Even {guardian.label_word} gave a small nod; "
            f"the new treat was a plain, honest way to put fairness back."
        )
    elif repair.id == "carry_bags_and_apologize":
        hero.memes["repair"] += 1
        hero.meters["carrying"] += 1
        world.say(
            f"Then {hero.id} asked to carry {guardian.label_word}'s shopping bags all the way to the shoe store "
            f"so {friend.id} could have both hands free and the first turn choosing ribbon. It was a kindly act, "
            f"yet it could not replace what had been eaten."
        )
    propagate(world, narrate=False)


def ending(world: World, stall: Stall, snack: Snack, repair: Repair) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    reconciled = friend.memes["hurt"] < THRESHOLD and friend.memes["trust"] >= THRESHOLD
    world.facts["reconciled"] = reconciled
    if reconciled:
        hero.memes["joy"] += 1
        friend.memes["joy"] += 1
        world.say(
            f"{friend.id} looked at {hero.id} for a long breath, then gave a small smile and stepped close again. "
            f'"Thank you for making it right," {friend.pronoun()} said. The shopping mall did not seem so large now.'
        )
        world.say(
            f"Soon the two friends were walking past bright windows once more, sharing the treat properly and "
            f"watching their reflections move together on the polished floor near {stall.label}."
        )
        world.say(
            "So the young ones learned this: a greedy chomp can crack a promise, "
            "but a truthful apology and a fair repair can mend it."
        )
    else:
        world.say(
            f"{friend.id} listened, and the anger grew smaller, but the hurt did not leave all at once. "
            f"{friend.pronoun().capitalize()} walked beside {hero.id} again, only with a little space still between them."
        )
        world.say(
            f"They passed the shining shop windows quietly. In the polished floor, {hero.id} could see the lesson "
            f"following {hero.pronoun('object')} step for step."
        )
        world.say(
            "And the lesson was this: when the harm is bigger than the repair, kindness must keep working until trust returns."
        )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    stall: Stall,
    snack: Snack,
    repair: Repair,
    coins: int = 1,
    bite: int = 1,
    pairing: Optional[Pairing] = None,
    guardian_type: str = "aunt",
) -> World:
    world = World()
    chosen_pairing = pairing or Pairing(
        hero_name="Pip",
        hero_type="fox",
        friend_name="Mina",
        friend_type="hen",
        relation_word="friends",
        elder_word="",
    )

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=chosen_pairing.hero_type,
        label=chosen_pairing.hero_name,
        role="hero",
        attrs={"coins": coins, "relation": chosen_pairing.relation_word},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=chosen_pairing.friend_type,
        label=chosen_pairing.friend_name,
        role="friend",
        attrs={"relation": chosen_pairing.relation_word},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_type,
        label="the grown-up",
        role="guardian",
        attrs={},
    ))
    snack_ent = world.add(Entity(
        id="snack",
        kind="thing",
        type="snack",
        label=snack.label,
        role="snack",
        attrs={"pieces_total": snack.pieces},
    ))
    mall = world.add(Entity(
        id="mall",
        kind="thing",
        type="place",
        label="shopping mall",
        role="place",
        attrs={},
    ))
    mall.meters["busy"] = 1.0
    friend.memes["trust"] = 1.0
    world.facts["promised_share"] = False

    opening(world, stall=stall, pairing=chosen_pairing, guardian=guardian)
    choose_treat(world, snack=snack)

    world.para()
    tempt(world, snack=snack)
    greedy_bite(world, snack=snack, bite=bite)
    walk_apart(world)

    world.para()
    notice_and_learn(world, repair=repair)
    apologize(world)
    do_repair(world, repair=repair, snack=snack, guardian=guardian)

    world.para()
    ending(world, stall=stall, snack=snack, repair=repair)

    world.facts.update(
        hero=hero,
        friend=friend,
        guardian=guardian,
        mall=mall,
        snack_cfg=snack,
        stall=stall,
        repair=repair,
        coins=coins,
        bite=bite,
        relation=chosen_pairing.relation_word,
        hero_name=chosen_pairing.hero_name,
        friend_name=chosen_pairing.friend_name,
        outcome="reconciled" if world.facts["reconciled"] else "still_hurt",
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
STALLS = {
    "pretzel_cart": Stall(
        id="pretzel_cart",
        label="the pretzel cart",
        smell="the smell of warm butter and salt",
        affords={"pretzel"},
        image="Twisted pretzels hung on little wooden pegs like golden loops.",
        tags={"mall", "pretzel"},
    ),
    "cookie_kiosk": Stall(
        id="cookie_kiosk",
        label="the cookie kiosk",
        smell="the sweet smell of butter and cinnamon",
        affords={"cookie"},
        image="Round cookies rested under glass, each one wider than a small paw.",
        tags={"mall", "cookie"},
    ),
    "popcorn_counter": Stall(
        id="popcorn_counter",
        label="the popcorn counter",
        smell="the smell of warm corn and sugar",
        affords={"popcorn"},
        image="Tall paper tubs stood in neat rows beside a bright red warmer.",
        tags={"mall", "popcorn"},
    ),
}

SNACKS = {
    "pretzel": Snack(
        id="pretzel",
        label="pretzel",
        phrase="one warm mall pretzel",
        share_name="one pretzel to share",
        bite_name="chomp",
        pieces=2,
        split_kind="loop",
        crunch_line="Salt scattered on the paper sleeve, and one side of the pretzel was suddenly smaller.",
        tags={"pretzel", "share"},
    ),
    "cookie": Snack(
        id="cookie",
        label="cookie",
        phrase="one big cinnamon cookie",
        share_name="one cookie to share",
        bite_name="chomp",
        pieces=2,
        split_kind="half",
        crunch_line="Crumbs skipped down like tiny pebbles, and the round cookie lost its balance.",
        tags={"cookie", "share"},
    ),
    "popcorn": Snack(
        id="popcorn",
        label="popcorn tub",
        phrase="one striped tub of sweet popcorn",
        share_name="one tub to share",
        bite_name="chomp",
        pieces=3,
        split_kind="handful",
        crunch_line="The top layer sank at once, and the tub no longer looked even.",
        tags={"popcorn", "share"},
    ),
}

REPAIRS = {
    "offer_best_piece": Repair(
        id="offer_best_piece",
        sense=2,
        power=2,
        needs_coin=0,
        needs_remaining=1,
        text="offered the best piece left",
        qa_text="offered the best unbitten part that was left",
        tags={"share", "apology"},
    ),
    "buy_replacement": Repair(
        id="buy_replacement",
        sense=3,
        power=3,
        needs_coin=1,
        needs_remaining=0,
        text="bought a fresh replacement treat",
        qa_text="used a spare coin to buy a fresh replacement treat",
        tags={"money", "apology"},
    ),
    "carry_bags_and_apologize": Repair(
        id="carry_bags_and_apologize",
        sense=2,
        power=1,
        needs_coin=0,
        needs_remaining=0,
        text="apologized and tried to help in another way",
        qa_text="apologized and tried to make up for it by helping carry shopping bags",
        tags={"apology", "bags"},
    ),
    "apology_only": Repair(
        id="apology_only",
        sense=1,
        power=1,
        needs_coin=0,
        needs_remaining=0,
        text="only apologized",
        qa_text="only apologized",
        tags={"apology"},
    ),
}

PAIRINGS = [
    Pairing(
        hero_name="Pip",
        hero_type="fox",
        friend_name="Mina",
        friend_type="hen",
        relation_word="friends",
        elder_word="",
    ),
    Pairing(
        hero_name="Tavi",
        hero_type="bear",
        friend_name="Rue",
        friend_type="doe",
        relation_word="cousins",
        elder_word="older cousin",
    ),
    Pairing(
        hero_name="Nell",
        hero_type="vixen",
        friend_name="Bram",
        friend_type="buck",
        relation_word="friends",
        elder_word="",
    ),
]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    stall: str
    snack: str
    repair: str
    coins: int
    bite: int
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    relation: str
    guardian: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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


KNOWLEDGE = {
    "mall": [(
        "What is a shopping mall?",
        "A shopping mall is a big building with many shops and walkways inside. People go there to buy things, eat snacks, and walk from store to store."
    )],
    "pretzel": [(
        "What is a pretzel?",
        "A pretzel is baked bread twisted into a loop shape and often sprinkled with salt. It can be soft and warm, which is why people like to share one fresh from a cart."
    )],
    "cookie": [(
        "Why do cookies make crumbs?",
        "Cookies can make crumbs because their baked edges break into tiny bits when you bite them. That is why a cookie can look smaller very quickly after one big bite."
    )],
    "popcorn": [(
        "What is popcorn?",
        "Popcorn is corn that puffs up when it gets hot. It is light and easy to share by handfuls."
    )],
    "money": [(
        "What does it mean to buy a replacement?",
        "Buying a replacement means getting a new thing to stand where the first one was spoiled or used up. It can be a fair way to make something right after a mistake."
    )],
    "apology": [(
        "What is an apology?",
        "An apology is when you plainly say you were wrong and that you are sorry. A good apology names the harm and does not pretend the hurt was small."
    )],
    "share": [(
        "Why is sharing a promise?",
        "When two people agree to share, each one is trusting the other to be fair. Breaking that promise can hurt feelings even if the thing is only a snack."
    )],
    "bags": [(
        "Why might helping with bags not fix everything?",
        "Helping with bags is kind, but it does not always repair the exact harm. If someone lost their fair share, the repair has to answer that loss in some honest way."
    )],
}
KNOWLEDGE_ORDER = ["mall", "pretzel", "cookie", "popcorn", "share", "apology", "money", "bags"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    snack = f["snack_cfg"]
    return [
        f'Write a short fable set in a shopping mall that includes the word "chomp" and ends with a lesson about fairness.',
        f"Tell a gentle reconciliation story where {hero.label} hurts {friend.label} by taking too much of a shared {snack.label}, then tries to make things right.",
        "Write a child-facing story in a polished indoor shopping mall, with a food-court treat, a broken promise, and a repaired friendship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    guardian = f["guardian"]
    stall = f["stall"]
    snack = f["snack_cfg"]
    repair = f["repair"]
    bite = f["bite"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label}, two young {f['relation']}, walking through a shopping mall with {guardian.label_word}. They stop for a shared treat and then have to face what fairness means."
        ),
        (
            f"Why was {friend.label} hurt?",
            f"{friend.label} was hurt because the treat was supposed to be shared, but {hero.label} took {bite} greedy bite{'s' if bite != 1 else ''} first. The hurt came from the broken promise, not only from the missing food."
        ),
        (
            "What changed the story in the middle?",
            f"The turn came when {hero.label} saw {friend.label}'s sad face reflected in the fountain water and understood what the greedy moment had done. That sight woke up guilt and pushed {hero.pronoun()} toward an apology instead of another excuse."
        ),
    ]
    if outcome == "reconciled":
        qa.append((
            f"How did {hero.label} and {friend.label} reconcile?",
            f"{hero.label} first admitted the wrong and said sorry, then {repair.qa_text}. That repair matched the harm closely enough that {friend.label} could trust {hero.pronoun('object')} again."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the two friends close together again, walking past the bright shop windows and sharing fairly. The final image shows the friendship restored, not just the snack replaced."
        ))
    else:
        qa.append((
            f"Why did the apology not fully fix the problem?",
            f"{hero.label} did try to make amends, but the repair was smaller than the hurt caused by the greedy bite. {friend.label} softened, yet some distance remained because trust needs a fair answer."
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly, with the two walking on together but not all the way mended. The polished mall floor reflected the lesson that some hurts take more work to heal."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"mall"} | set(world.facts["stall"].tags) | set(world.facts["snack_cfg"].tags)
    tags |= set(world.facts["repair"].tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: {{'outcome': {world.facts.get('outcome')!r}, 'bite': {world.facts.get('bite')!r}, 'coins': {world.facts.get('coins')!r}}}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        stall="pretzel_cart",
        snack="pretzel",
        repair="offer_best_piece",
        coins=0,
        bite=1,
        hero_name="Pip",
        hero_type="fox",
        friend_name="Mina",
        friend_type="hen",
        relation="friends",
        guardian="aunt",
        seed=None,
    ),
    StoryParams(
        stall="cookie_kiosk",
        snack="cookie",
        repair="buy_replacement",
        coins=1,
        bite=2,
        hero_name="Nell",
        hero_type="vixen",
        friend_name="Bram",
        friend_type="buck",
        relation="friends",
        guardian="uncle",
        seed=None,
    ),
    StoryParams(
        stall="popcorn_counter",
        snack="popcorn",
        repair="carry_bags_and_apologize",
        coins=0,
        bite=2,
        hero_name="Tavi",
        hero_type="bear",
        friend_name="Rue",
        friend_type="doe",
        relation="cousins",
        guardian="aunt",
        seed=None,
    ),
    StoryParams(
        stall="popcorn_counter",
        snack="popcorn",
        repair="offer_best_piece",
        coins=0,
        bite=1,
        hero_name="Pip",
        hero_type="fox",
        friend_name="Rue",
        friend_type="doe",
        relation="friends",
        guardian="uncle",
        seed=None,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(Stall, Snack, Repair, Coins, Bite) :-
    stall(Stall), snack(Snack), repair(Repair), coins(Coins), bite(Bite),
    sold_here(Stall, Snack),
    sensible(Repair),
    pieces(Snack, P), Bite <= P,
    remains(Snack, Bite, Rem),
    need_coin(Repair, NC), Coins >= NC,
    need_remaining(Repair, NR), Rem >= NR.

sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.

remains(Snack, Bite, Rem) :- pieces(Snack, P), bite(Bite), Rem = P - Bite.

% --- outcome model ---------------------------------------------------------
reconciled :-
    chosen_repair(R), chosen_snack(S), chosen_bite(B), chosen_coins(C),
    need_coin(R, NC), C >= NC,
    remains(S, B, Rem), need_remaining(R, NR), Rem >= NR,
    power(R, P), severity(B).

severity(B) :- chosen_bite(B).

ok_repair :-
    chosen_repair(R), chosen_snack(S), chosen_bite(B), chosen_coins(C),
    need_coin(R, NC), C >= NC,
    remains(S, B, Rem), need_remaining(R, NR), Rem >= NR.

reconciled :- ok_repair, chosen_repair(R), chosen_bite(B), power(R, P), P >= B.
outcome(reconciled) :- reconciled.
outcome(still_hurt) :- not reconciled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for stall_id, stall in STALLS.items():
        lines.append(asp.fact("stall", stall_id))
        for snack_id in sorted(stall.affords):
            lines.append(asp.fact("sold_here", stall_id, snack_id))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        lines.append(asp.fact("pieces", snack_id, snack.pieces))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("power", repair_id, repair.power))
        lines.append(asp.fact("need_coin", repair_id, repair.needs_coin))
        lines.append(asp.fact("need_remaining", repair_id, repair.needs_remaining))
    for coins in (0, 1, 2):
        lines.append(asp.fact("coins", coins))
    for bite in (1, 2):
        lines.append(asp.fact("bite", bite))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_repair", params.repair),
        asp.fact("chosen_snack", params.snack),
        asp.fact("chosen_bite", params.bite),
        asp.fact("chosen_coins", params.coins),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    snack = SNACKS[params.snack]
    repair = REPAIRS[params.repair]
    return "reconciled" if is_reconciled(repair=repair, snack=snack, bite=params.bite, coins=params.coins) else "still_hurt"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed during verify for seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Empty story from smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a greedy chomp in a shopping mall and the work of reconciliation."
    )
    ap.add_argument("--stall", choices=sorted(STALLS))
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--repair", choices=sorted(REPAIRS))
    ap.add_argument("--coins", type=int, choices=[0, 1, 2])
    ap.add_argument("--bite", type=int, choices=[1, 2])
    ap.add_argument("--guardian", choices=["aunt", "uncle", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stall and args.snack:
        if not sold_here(stall=STALLS[args.stall], snack=SNACKS[args.snack]):
            raise StoryError(explain_sale(stall=STALLS[args.stall], snack=SNACKS[args.snack]))

    if args.bite is not None and args.snack is not None and args.bite > SNACKS[args.snack].pieces:
        raise StoryError(f"(No story: a {SNACKS[args.snack].label} cannot lose {args.bite} bites here.)")

    if args.repair and args.snack and args.coins is not None and args.bite is not None:
        if not can_perform_repair(
            repair=REPAIRS[args.repair],
            snack=SNACKS[args.snack],
            bite=args.bite,
            coins=args.coins,
        ):
            raise StoryError(explain_repair(
                repair=REPAIRS[args.repair],
                snack=SNACKS[args.snack],
                bite=args.bite,
                coins=args.coins,
            ))
        if REPAIRS[args.repair].sense < SENSE_MIN:
            raise StoryError(
                f"(Refusing repair '{args.repair}': it scores too low on common sense "
                f"(sense={REPAIRS[args.repair].sense} < {SENSE_MIN}).)"
            )

    combos = [
        combo for combo in valid_combos()
        if (args.stall is None or combo[0] == args.stall)
        and (args.snack is None or combo[1] == args.snack)
        and (args.repair is None or combo[2] == args.repair)
        and (args.coins is None or combo[3] == args.coins)
        and (args.bite is None or combo[4] == args.bite)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    stall_id, snack_id, repair_id, coins, bite = rng.choice(sorted(combos))
    pairing = rng.choice(PAIRINGS)
    guardian = args.guardian or rng.choice(["aunt", "uncle", "mother", "father"])
    return StoryParams(
        stall=stall_id,
        snack=snack_id,
        repair=repair_id,
        coins=coins,
        bite=bite,
        hero_name=pairing.hero_name,
        hero_type=pairing.hero_type,
        friend_name=pairing.friend_name,
        friend_type=pairing.friend_type,
        relation=pairing.relation_word,
        guardian=guardian,
        seed=None,
    )


def _pairing_from_params(params: StoryParams) -> Pairing:
    return Pairing(
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        relation_word=params.relation,
        elder_word="",
    )


def generate(params: StoryParams) -> StorySample:
    if params.stall not in STALLS:
        raise StoryError(f"Unknown stall: {params.stall}")
    if params.snack not in SNACKS:
        raise StoryError(f"Unknown snack: {params.snack}")
    if params.repair not in REPAIRS:
        raise StoryError(f"Unknown repair: {params.repair}")
    if params.bite not in (1, 2):
        raise StoryError("bite must be 1 or 2")
    if params.coins not in (0, 1, 2):
        raise StoryError("coins must be 0, 1, or 2")
    stall = STALLS[params.stall]
    snack = SNACKS[params.snack]
    repair = REPAIRS[params.repair]

    if not sold_here(stall=stall, snack=snack):
        raise StoryError(explain_sale(stall=stall, snack=snack))
    if repair.sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing repair '{params.repair}': it scores too low on common sense "
            f"(sense={repair.sense} < {SENSE_MIN}).)"
        )
    if not can_perform_repair(repair=repair, snack=snack, bite=params.bite, coins=params.coins):
        raise StoryError(explain_repair(repair=repair, snack=snack, bite=params.bite, coins=params.coins))

    world = tell(
        stall=stall,
        snack=snack,
        repair=repair,
        coins=params.coins,
        bite=params.bite,
        pairing=_pairing_from_params(params),
        guardian_type=params.guardian,
    )
    story = world.render().replace("hero", params.hero_name).replace("friend", params.friend_name)
    story = story.replace("guardian", world.get("guardian").label_word)
    story = story.replace("snack", snack.label)

    story = story.replace(" hero ", f" {params.hero_name} ")
    story = story.replace(" friend ", f" {params.friend_name} ")

    story = story.replace("hero.id", params.hero_name).replace("friend.id", params.friend_name)

    story = story.replace(world.get("hero").id, params.hero_name)
    story = story.replace(world.get("friend").id, params.friend_name)
    world.get("hero").id = params.hero_name
    world.get("friend").id = params.friend_name

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (stall, snack, repair, coins, bite) combos:\n")
        for stall, snack, repair, coins, bite in combos:
            print(f"  {stall:16} {snack:8} {repair:24} coins={coins} bite={bite}")
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
            header = (
                f"### {p.hero_name} & {p.friend_name}: {p.snack} at {p.stall} "
                f"({p.repair}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
