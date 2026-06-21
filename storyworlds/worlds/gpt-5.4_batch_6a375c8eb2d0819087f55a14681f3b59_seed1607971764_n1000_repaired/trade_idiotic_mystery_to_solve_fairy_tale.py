#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trade_idiotic_mystery_to_solve_fairy_tale.py
=======================================================================

A standalone storyworld for a tiny fairy-tale mystery: at a market of small
trades, a child's treasured keepsake goes missing, a foolish rumor points at the
wrong creature, and a patient helper solves the mystery by following a physical
clue left by the trade itself.

The world prefers a narrower set of plausible stories over broad coverage:
a trade good leaves a specific residue or snag, and the keepsake can only be
found in a hiding place that honestly matches that clue. Unreasonable pairings
are rejected with a legible explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/trade_idiotic_mystery_to_solve_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/trade_idiotic_mystery_to_solve_fairy_tale.py --trade_good honeycomb --hiding_place apron_fold
    python storyworlds/worlds/gpt-5.4/trade_idiotic_mystery_to_solve_fairy_tale.py --trade_good honeycomb --hiding_place flour_bin
    python storyworlds/worlds/gpt-5.4/trade_idiotic_mystery_to_solve_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/trade_idiotic_mystery_to_solve_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/trade_idiotic_mystery_to_solve_fairy_tale.py --verify
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
        female = {"girl", "mother", "queen", "witch", "woman"}
        male = {"boy", "father", "king", "wizard", "man", "dwarf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "owl": "owl",
            "fox": "fox",
            "dwarf": "dwarf",
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
class Kingdom:
    id: str
    place: str
    opening: str
    market: str
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
class LostItem:
    id: str
    label: str
    phrase: str
    shine: str
    keepsake_from: str
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
class TradeGood:
    id: str
    label: str
    phrase: str
    residue: str
    residue_text: str
    action: str
    carry_text: str
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    accepts: set[str]
    clue_text: str
    reveal_text: str
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
    type: str
    title: str
    manner: str
    clue_style: str
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
class Rumor:
    id: str
    suspect: str
    line: str
    why_wrong: str
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


def _r_hide_item(world: World) -> list[str]:
    token = world.get("token")
    spot = world.get("spot")
    clue = str(world.facts.get("trade_residue", ""))
    if token.meters["mislaid"] < THRESHOLD:
        return []
    sig = ("hide_item", clue, spot.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if clue in spot.attrs.get("accepts", set()):
        token.meters["hidden"] += 1
        spot.meters["holds_token"] += 1
        spot.meters[clue] += 1
        return ["__hidden__"]
    return []


def _r_worry(world: World) -> list[str]:
    hero = world.get("hero")
    token = world.get("token")
    if token.meters["hidden"] < THRESHOLD:
        return []
    sig = ("worry", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["love_token"] += 1
    return ["__worry__"]


def _r_rumor(world: World) -> list[str]:
    crowd = world.get("crowd")
    if world.facts.get("rumor_spoken") is not True:
        return []
    sig = ("rumor", crowd.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.memes["suspicion"] += 1
    crowd.memes["confusion"] += 1
    return ["__rumor__"]


def _r_find(world: World) -> list[str]:
    helper = world.get("helper")
    token = world.get("token")
    spot = world.get("spot")
    clue = str(world.facts.get("trade_residue", ""))
    if helper.meters["inspecting"] < THRESHOLD:
        return []
    if token.meters["hidden"] < THRESHOLD:
        return []
    sig = ("find", helper.id, spot.id)
    if sig in world.fired:
        return []
    if clue not in spot.attrs.get("accepts", set()):
        return []
    world.fired.add(sig)
    token.meters["found"] += 1
    token.meters["hidden"] = 0.0
    spot.meters["holds_token"] = 0.0
    hero = world.get("hero")
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    helper.memes["calm"] += 1
    return ["__found__"]


CAUSAL_RULES = [
    Rule(name="hide_item", tag="physical", apply=_r_hide_item),
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="rumor", tag="social", apply=_r_rumor),
    Rule(name="find", tag="resolution", apply=_r_find),
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


def clue_matches(trade_good: TradeGood, hiding_place: HidingPlace) -> bool:
    return trade_good.residue in hiding_place.accepts


def explain_rejection(trade_good: TradeGood, hiding_place: HidingPlace) -> str:
    accepts = ", ".join(sorted(hiding_place.accepts))
    return (
        f"(No story: {trade_good.label} leaves a {trade_good.residue} clue, but "
        f"{hiding_place.phrase} only fits clues like {accepts}. The mystery must be "
        f"solved by a real trail left by the trade, so pick a matching hiding place.)"
    )


def predict_solution(trade_good: TradeGood, hiding_place: HidingPlace) -> dict:
    return {
        "solvable": clue_matches(trade_good, hiding_place),
        "residue": trade_good.residue,
        "spot": hiding_place.label,
    }


KINGDOMS = {
    "moonbrook": Kingdom(
        id="moonbrook",
        place="Moonbrook",
        opening="Beyond seven reeds and a silver stream stood Moonbrook, a village where market bells sounded soft as spoons in teacups.",
        market="In the middle of the square, traders spread their wares beneath fluttering banners and lanterns shaped like pears.",
        closing="That night the stream shone with a pale ribbon of moonlight, and the square felt wiser than it had that morning.",
        tags={"village", "market"},
    ),
    "thistledown": Kingdom(
        id="thistledown",
        place="Thistledown",
        opening="On the edge of Thistledown, where hedges curled like green crowns, a fair opened whenever the sun liked the look of the day.",
        market="Stall cloths sparkled with dew, and tiny brass bells chimed whenever someone made a trade.",
        closing="By evening the hedges held the sunset in their thorns like threads of red gold.",
        tags={"village", "fair"},
    ),
    "amberfen": Kingdom(
        id="amberfen",
        place="Amberfen",
        opening="Past the amber reeds of a quiet fen lay a bright little town where stories and apples were traded almost as often as coins.",
        market="The market stood beside a round old well, and every stall seemed to glow as if a kind spell lived under the cloth.",
        closing="When dusk leaned over the fen, the well kept one last ring of light on its stones.",
        tags={"village", "well"},
    ),
}

LOST_ITEMS = {
    "moon_locket": LostItem(
        id="moon_locket",
        label="moon locket",
        phrase="a small moon locket",
        shine="caught the light like a drop of milk",
        keepsake_from="grandmother",
        tags={"keepsake", "silver"},
    ),
    "bell_charm": LostItem(
        id="bell_charm",
        label="bell charm",
        phrase="a tiny bell charm",
        shine="gave off a shy golden blink",
        keepsake_from="grandmother",
        tags={"keepsake", "gold"},
    ),
    "star_pin": LostItem(
        id="star_pin",
        label="star pin",
        phrase="a little star pin",
        shine="winked like a star in shallow water",
        keepsake_from="grandmother",
        tags={"keepsake", "star"},
    ),
}

TRADE_GOODS = {
    "honeycomb": TradeGood(
        id="honeycomb",
        label="honeycomb",
        phrase="a square of honeycomb wrapped in leaves",
        residue="sticky",
        residue_text="a little gold stickiness",
        action="trade a polished pebble for honeycomb",
        carry_text="The honeycomb dripped one bright thread of honey onto the cloth.",
        tags={"trade", "honey"},
    ),
    "flour_sack": TradeGood(
        id="flour_sack",
        label="flour sack",
        phrase="a paper sack of flour for cake-making",
        residue="powdery",
        residue_text="a pale white dust",
        action="trade a ribbon spool for a small flour sack",
        carry_text="The flour sack left a soft puff of white on sleeve and basket rim.",
        tags={"trade", "flour"},
    ),
    "violet_ribbon": TradeGood(
        id="violet_ribbon",
        label="violet ribbon",
        phrase="a coil of violet ribbon",
        residue="silky",
        residue_text="one shining violet thread",
        action="trade a walnut shell boat for violet ribbon",
        carry_text="The ribbon slid so smooth that one loose thread floated after it.",
        tags={"trade", "ribbon"},
    ),
    "plum_basket": TradeGood(
        id="plum_basket",
        label="plum basket",
        phrase="a basket of dark plums",
        residue="purple",
        residue_text="a dab of plum-purple juice",
        action="trade three copper buttons for a basket of plums",
        carry_text="One plum split with a tiny pop and marked the handle with purple juice.",
        tags={"trade", "plum"},
    ),
}

HIDING_PLACES = {
    "basket_lining": HidingPlace(
        id="basket_lining",
        label="basket lining",
        phrase="the lining of the market basket",
        accepts={"sticky"},
        clue_text="The basket lining held a gleam of honey where no honey should have been.",
        reveal_text="There, pressed to the basket lining, hung the missing keepsake.",
        tags={"basket"},
    ),
    "apron_fold": HidingPlace(
        id="apron_fold",
        label="apron fold",
        phrase="the folded corner of the baker's apron",
        accepts={"powdery"},
        clue_text="In one apron fold lay a crescent of white dust, neat as a moon on dark cloth.",
        reveal_text="There, tucked inside the apron fold, rested the missing keepsake.",
        tags={"apron"},
    ),
    "thorn_hook": HidingPlace(
        id="thorn_hook",
        label="thorn hook",
        phrase="a thorn hook on the ribbon stall",
        accepts={"silky"},
        clue_text="A violet thread trembled on one thorn as if it were trying to point the way.",
        reveal_text="There, caught below the thorn hook, glittered the missing keepsake.",
        tags={"thorn", "ribbon"},
    ),
    "crate_slat": HidingPlace(
        id="crate_slat",
        label="crate slat",
        phrase="the slat of a plum crate",
        accepts={"purple"},
        clue_text="A purple thumbprint shone on the wood, fresh and juicy.",
        reveal_text="There, behind the crate slat, waited the missing keepsake.",
        tags={"crate", "plum"},
    ),
}

HELPERS = {
    "owl": HelperCfg(
        id="owl",
        type="owl",
        title="Old Owl",
        manner="blinked once and spoke in a quiet, exact voice",
        clue_style="followed little signs the way other people followed roads",
        tags={"owl", "wisdom"},
    ),
    "fox": HelperCfg(
        id="fox",
        type="fox",
        title="Fox Clerk",
        manner="smoothed his vest and narrowed his clever eyes",
        clue_style="noticed what everyone else had stepped past",
        tags={"fox", "wisdom"},
    ),
    "dwarf": HelperCfg(
        id="dwarf",
        type="dwarf",
        title="Mossbeard",
        manner="tapped the cobbles with a tiny hammer and hummed while thinking",
        clue_style="trusted crumbs and threads more than loud guesses",
        tags={"dwarf", "wisdom"},
    ),
}

RUMORS = {
    "magpie": Rumor(
        id="magpie",
        suspect="the magpie",
        line='"The magpie took it!" cried someone from the onion stall.',
        why_wrong="The magpie had been busy stealing only shiny bottle caps all week, and had never once flown near the trade table.",
        tags={"bird", "rumor"},
    ),
    "goblin": Rumor(
        id="goblin",
        suspect="the turnip goblin",
        line='"The turnip goblin must have pocketed it!" muttered a cobbler.',
        why_wrong="The turnip goblin did not even have pockets, only a muddy apron and a look of deep sleepiness.",
        tags={"goblin", "rumor"},
    ),
    "cat": Rumor(
        id="cat",
        suspect="the palace cat",
        line='"It was the palace cat!" said the jam seller at once.',
        why_wrong="The palace cat hated the market and would not come within ten whiskers of the crowd.",
        tags={"cat", "rumor"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Tansy", "Nora", "Lila", "Poppy", "Wren", "Aster"]
BOY_NAMES = ["Ivo", "Tobin", "Milo", "Rowan", "Bram", "Finn", "Ned", "Orrin"]
TRAITS = ["curious", "gentle", "bright", "careful", "hopeful", "earnest"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for kingdom_id in KINGDOMS:
        for trade_id, trade_good in TRADE_GOODS.items():
            for hiding_id, hiding_place in HIDING_PLACES.items():
                if clue_matches(trade_good, hiding_place):
                    combos.append((kingdom_id, trade_id, hiding_id))
    return combos


@dataclass
class StoryParams:
    kingdom: str
    lost_item: str
    trade_good: str
    hiding_place: str
    helper: str
    rumor: str
    hero_name: str
    hero_gender: str
    trait: str
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


def introduce(world: World, kingdom: Kingdom, hero: Entity, token: Entity, lost_item: LostItem) -> None:
    hero.memes["joy"] += 1
    token.memes["cherished"] += 1
    world.say(kingdom.opening)
    world.say(
        f"There lived {hero.id}, a {next(iter(hero.traits), 'curious')} little {hero.type}, "
        f"who wore {lost_item.phrase} that {lost_item.shine}."
    )
    world.say(
        f"It had come from {hero.attrs['gift_from']}, so {hero.id} touched it whenever "
        f"{hero.pronoun()} wanted to feel brave."
    )
    world.say(kingdom.market)


def make_trade(world: World, hero: Entity, trade_good: TradeGood) -> None:
    hero.meters["traded"] += 1
    world.facts["trade_residue"] = trade_good.residue
    world.say(
        f"That morning {hero.id} went to the fair to {trade_good.action}. "
        f"The trade seemed simple and merry."
    )
    world.say(trade_good.carry_text)
    world.say(
        f"{hero.id} laughed, tucked the new thing close, and hurried on before the bells stopped chiming."
    )


def lose_item(world: World, hero: Entity, token: Entity) -> None:
    token.meters["mislaid"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Yet halfway across the square, {hero.id}'s hand flew to {hero.pronoun('possessive')} throat."
    )
    world.say(
        f"The {token.label} was gone. At once the market seemed too large, and every bright stall looked full of questions."
    )


def spread_rumor(world: World, hero: Entity, helper: Entity, rumor: Rumor) -> None:
    world.facts["rumor_spoken"] = True
    propagate(world, narrate=False)
    world.say(rumor.line)
    world.say(
        f"A few heads turned, and the mystery began to wobble in the wrong direction."
    )
    world.say(
        f'{helper.id} {helper.attrs["manner"]}. "That is an idiotic guess," {helper.pronoun()} said. '
        f'"A missing thing is not the same as a stolen thing."'
    )
    world.say(rumor.why_wrong)


def inspect_clue(world: World, hero: Entity, helper: Entity, trade_good: TradeGood, hiding_place: HidingPlace) -> None:
    helper.meters["inspecting"] += 1
    world.say(
        f"Then {helper.id} looked at {hero.id}'s fingers, at the traded goods, and at the path back through the stalls."
    )
    world.say(
        f"{helper.pronoun().capitalize()} {helper.attrs['clue_style']}. "
        f'"See here," {helper.pronoun()} said. "There is {trade_good.residue_text}. '
        f'Mysteries speak softly, but they do speak."'
    )
    world.say(hiding_place.clue_text)
    propagate(world, narrate=False)


def recover_item(world: World, hero: Entity, helper: Entity, token: Entity, hiding_place: HidingPlace) -> None:
    world.say(
        f"{helper.id} reached carefully toward {hiding_place.phrase}."
    )
    world.say(hiding_place.reveal_text)
    world.say(
        f"{hero.id} gave such a sigh of relief that even the cabbage leaves by the well seemed to relax."
    )
    world.say(
        f'"Thank you," {hero.id} whispered. "I nearly believed the loud voices instead of the little clues."'
    )


def ending(world: World, kingdom: Kingdom, hero: Entity, helper: Entity, token: Entity, trade_good: TradeGood) -> None:
    hero.memes["gratitude"] += 1
    helper.memes["pride"] += 1
    world.say(
        f'{helper.id} smiled. "The fairest trade in any kingdom," {helper.pronoun()} said, '
        f'"is when hurry is traded for thought."'
    )
    world.say(
        f"{hero.id} fastened the {token.label} safely again, finished carrying the {trade_good.label}, "
        f"and walked one slow circle around the square before going home."
    )
    world.say(kingdom.closing)


def tell(
    kingdom: Kingdom,
    lost_item: LostItem,
    trade_good: TradeGood,
    hiding_place: HidingPlace,
    helper_cfg: HelperCfg,
    rumor: Rumor,
    hero_name: str,
    hero_gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            attrs={"gift_from": lost_item.keepsake_from},
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.title,
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.title,
            role="helper",
            attrs={
                "manner": helper_cfg.manner,
                "clue_style": helper_cfg.clue_style,
            },
        )
    )
    crowd = world.add(
        Entity(
            id="Crowd",
            kind="character",
            type="folk",
            label="the market crowd",
            role="crowd",
        )
    )
    token = world.add(
        Entity(
            id="token",
            kind="thing",
            type="keepsake",
            label=lost_item.label,
            role="token",
        )
    )
    spot = world.add(
        Entity(
            id="spot",
            kind="thing",
            type="place",
            label=hiding_place.label,
            role="spot",
            attrs={"accepts": set(hiding_place.accepts)},
        )
    )

    world.facts.update(
        kingdom=kingdom,
        lost_item=lost_item,
        trade_good=trade_good,
        hiding_place=hiding_place,
        helper_cfg=helper_cfg,
        rumor=rumor,
        hero=hero,
        helper=helper,
        crowd=crowd,
        token=token,
        trade_residue=trade_good.residue,
        rumor_spoken=False,
    )

    introduce(world, kingdom, hero, token, lost_item)
    world.para()
    make_trade(world, hero, trade_good)
    lose_item(world, hero, token)
    world.para()
    spread_rumor(world, hero, helper, rumor)
    inspect_clue(world, hero, helper, trade_good, hiding_place)
    world.para()
    recover_item(world, hero, helper, token, hiding_place)
    ending(world, kingdom, hero, helper, token, trade_good)

    world.facts.update(
        solved=token.meters["found"] >= THRESHOLD,
        hidden=token.meters["hidden"] >= THRESHOLD,
        residue=trade_good.residue,
        suspect=rumor.suspect,
    )
    return world


KNOWLEDGE = {
    "trade": [
        (
            "What is a trade?",
            "A trade is when two people give each other things they both agree to exchange. It can be fair when both sides understand what they are giving and getting."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery?",
            "You look for clues and ask what really happened step by step. Good clues are small signs that can be checked, not just wild guesses."
        )
    ],
    "rumor": [
        (
            "Why can a rumor be a problem?",
            "A rumor can send people toward the wrong answer before they know the truth. That is unfair, because blaming first can hurt someone who did nothing wrong."
        )
    ],
    "owl": [
        (
            "Why are owls often shown as wise in fairy tales?",
            "Fairy tales often use owls as wise helpers because they are quiet watchers. They fit stories where someone must notice what others miss."
        )
    ],
    "fox": [
        (
            "Why is a fox a good mystery helper in a fairy tale?",
            "A fox is often shown as sharp-eyed and quick-thinking in fairy tales. That makes a fox a believable helper when a clue is small and easy to miss."
        )
    ],
    "dwarf": [
        (
            "Why might a dwarf solve a mystery carefully?",
            "A fairy-tale dwarf is often patient with little objects and hidden places. That patience helps when the answer is tucked somewhere small."
        )
    ],
    "honey": [
        (
            "Why is honey a useful clue?",
            "Honey is sticky, so it clings to fingers, cloth, and baskets. If something carries honey, it can leave a bright trail behind."
        )
    ],
    "flour": [
        (
            "Why is flour easy to track?",
            "Flour is a light powder, so it dusts sleeves and dark cloth very clearly. Even a little puff can show where something has been."
        )
    ],
    "ribbon": [
        (
            "How can a ribbon leave a clue?",
            "A ribbon can snag and leave behind a loose thread. That thread can point to the place where it caught."
        )
    ],
    "plum": [
        (
            "Why do plums make good evidence?",
            "Plums can burst and leave purple juice. A bright stain is easy to spot on wood or cloth."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "trade",
    "mystery",
    "rumor",
    "owl",
    "fox",
    "dwarf",
    "honey",
    "flour",
    "ribbon",
    "plum",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper_cfg = f["helper_cfg"]
    lost_item = f["lost_item"]
    trade_good = f["trade_good"]
    rumor = f["rumor"]
    return [
        (
            f'Write a short fairy tale for a 3-to-5-year-old where a child makes a trade, '
            f'loses {lost_item.phrase}, and solves a mystery by following a clue left by {trade_good.label}. '
            f'Include the words "trade" and "idiotic".'
        ),
        (
            f"Tell a gentle mystery-to-solve fairy tale where {hero.id} is misled by a rumor about "
            f"{rumor.suspect}, but {helper_cfg.title} notices the real clue and finds the missing keepsake."
        ),
        (
            f'Write a fairy-tale story in which an "idiotic guess" is rejected, and the true answer comes from '
            f'careful looking rather than blaming.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    lost_item = f["lost_item"]
    trade_good = f["trade_good"]
    hiding_place = f["hiding_place"]
    rumor = f["rumor"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who went to a fairy market with {lost_item.phrase}, and {helper.id}, who helped solve the mystery. The story follows how a small trade turned into a puzzle and then into a lesson."
        ),
        (
            f"What happened after {hero.id} made the trade?",
            f"After the trade, {hero.id} discovered that the {lost_item.label} was missing. The problem began right after carrying {trade_good.label}, so the trade itself became the first place to look for clues."
        ),
        (
            "Why was the rumor a bad idea?",
            f"The rumor blamed {rumor.suspect} before anyone had real evidence. That was unfair, and {helper.id} called it an idiotic guess because a mystery should be solved by clues, not by loud pointing."
        ),
        (
            f"How did {helper.id} solve the mystery?",
            f"{helper.id} noticed {trade_good.residue_text} and followed that clue to {hiding_place.phrase}. The physical trail matched the place where the keepsake had caught, so the answer came from what the world showed, not from guessing."
        ),
        (
            f"Where was the {lost_item.label}?",
            f"It was at {hiding_place.phrase}. That place fit the clue left by {trade_good.label}, which is why the search worked."
        ),
        (
            "How did the story end?",
            f"The keepsake was found, and {hero.id} fastened it safely again before going home. The ending shows that the market became peaceful once the truth was discovered."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper_cfg = f["helper_cfg"]
    trade_good = f["trade_good"]
    tags = {"trade", "mystery", "rumor"} | set(helper_cfg.tags) | set(trade_good.tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {}
            for key, val in ent.attrs.items():
                shown[key] = sorted(val) if isinstance(val, set) else val
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_matches(T, H) :- trade_good(T), hiding_place(H), leaves(T, R), accepts(H, R).
valid(K, T, H) :- kingdom(K), clue_matches(T, H).

outcome(solved) :- chosen_trade(T), chosen_hiding(H), clue_matches(T, H).
outcome(unsolved) :- chosen_trade(T), chosen_hiding(H), not clue_matches(T, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for kingdom_id in KINGDOMS:
        lines.append(asp.fact("kingdom", kingdom_id))
    for trade_id, trade_good in TRADE_GOODS.items():
        lines.append(asp.fact("trade_good", trade_id))
        lines.append(asp.fact("leaves", trade_id, trade_good.residue))
    for hiding_id, hiding_place in HIDING_PLACES.items():
        lines.append(asp.fact("hiding_place", hiding_id))
        for residue in sorted(hiding_place.accepts):
            lines.append(asp.fact("accepts", hiding_id, residue))
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
            asp.fact("chosen_trade", params.trade_good),
            asp.fact("chosen_hiding", params.hiding_place),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        kingdom="moonbrook",
        lost_item="moon_locket",
        trade_good="honeycomb",
        hiding_place="basket_lining",
        helper="owl",
        rumor="magpie",
        hero_name="Elin",
        hero_gender="girl",
        trait="curious",
    ),
    StoryParams(
        kingdom="thistledown",
        lost_item="bell_charm",
        trade_good="flour_sack",
        hiding_place="apron_fold",
        helper="dwarf",
        rumor="goblin",
        hero_name="Tobin",
        hero_gender="boy",
        trait="careful",
    ),
    StoryParams(
        kingdom="amberfen",
        lost_item="star_pin",
        trade_good="violet_ribbon",
        hiding_place="thorn_hook",
        helper="fox",
        rumor="cat",
        hero_name="Lila",
        hero_gender="girl",
        trait="bright",
    ),
    StoryParams(
        kingdom="moonbrook",
        lost_item="bell_charm",
        trade_good="plum_basket",
        hiding_place="crate_slat",
        helper="owl",
        rumor="goblin",
        hero_name="Milo",
        hero_gender="boy",
        trait="gentle",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale mystery storyworld: a market trade, a missing keepsake, and a clue-led solution."
    )
    ap.add_argument("--kingdom", choices=KINGDOMS)
    ap.add_argument("--lost_item", choices=LOST_ITEMS)
    ap.add_argument("--trade_good", choices=TRADE_GOODS)
    ap.add_argument("--hiding_place", choices=HIDING_PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--hero_name")
    ap.add_argument("--hero_gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trade_good and args.hiding_place:
        trade_good = TRADE_GOODS[args.trade_good]
        hiding_place = HIDING_PLACES[args.hiding_place]
        if not clue_matches(trade_good, hiding_place):
            raise StoryError(explain_rejection(trade_good, hiding_place))

    combos = [
        combo
        for combo in valid_combos()
        if (args.kingdom is None or combo[0] == args.kingdom)
        and (args.trade_good is None or combo[1] == args.trade_good)
        and (args.hiding_place is None or combo[2] == args.hiding_place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    kingdom_id, trade_id, hiding_id = rng.choice(sorted(combos))
    lost_item = args.lost_item or rng.choice(sorted(LOST_ITEMS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    rumor = args.rumor or rng.choice(sorted(RUMORS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    trait = rng.choice(TRAITS)

    return StoryParams(
        kingdom=kingdom_id,
        lost_item=lost_item,
        trade_good=trade_id,
        hiding_place=hiding_id,
        helper=helper,
        rumor=rumor,
        hero_name=hero_name,
        hero_gender=hero_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.kingdom not in KINGDOMS:
        raise StoryError(f"(Unknown kingdom: {params.kingdom})")
    if params.lost_item not in LOST_ITEMS:
        raise StoryError(f"(Unknown lost_item: {params.lost_item})")
    if params.trade_good not in TRADE_GOODS:
        raise StoryError(f"(Unknown trade_good: {params.trade_good})")
    if params.hiding_place not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding_place: {params.hiding_place})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.rumor not in RUMORS:
        raise StoryError(f"(Unknown rumor: {params.rumor})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero_gender: {params.hero_gender})")

    trade_good = TRADE_GOODS[params.trade_good]
    hiding_place = HIDING_PLACES[params.hiding_place]
    if not clue_matches(trade_good, hiding_place):
        raise StoryError(explain_rejection(trade_good, hiding_place))

    world = tell(
        kingdom=KINGDOMS[params.kingdom],
        lost_item=LOST_ITEMS[params.lost_item],
        trade_good=trade_good,
        hiding_place=hiding_place,
        helper_cfg=HELPERS[params.helper],
        rumor=RUMORS[params.rumor],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
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


def _python_outcome(params: StoryParams) -> str:
    return "solved" if clue_matches(TRADE_GOODS[params.trade_good], HIDING_PLACES[params.hiding_place]) else "unsolved"


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
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        ao = asp_outcome(params)
        po = _python_outcome(params)
        if ao != po:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

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
        print(f"{len(combos)} compatible (kingdom, trade_good, hiding_place) combos:\n")
        for kingdom_id, trade_id, hiding_id in combos:
            print(f"  {kingdom_id:11} {trade_id:13} {hiding_id}")
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
            header = (
                f"### {p.hero_name}: {p.trade_good} -> {p.hiding_place} "
                f"({p.kingdom}, helper={p.helper})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
