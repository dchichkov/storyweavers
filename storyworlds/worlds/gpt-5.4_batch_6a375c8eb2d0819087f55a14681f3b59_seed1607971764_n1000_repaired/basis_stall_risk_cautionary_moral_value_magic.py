#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/basis_stall_risk_cautionary_moral_value_magic.py
============================================================================

A standalone storyworld for a small fable-like market tale:

A young animal helps at a village stall. Some goods are no longer good enough
to sell, and a tempting magic trick could make them look perfect for a while.
A wiser helper warns about the risk. If the youngster uses the glamour anyway,
the market's trust is harmed and an elder must choose an honest repair. The
moral is clear: honesty is the basis of a good stall.

Run it
------
    python storyworlds/worlds/gpt-5.4/basis_stall_risk_cautionary_moral_value_magic.py
    python storyworlds/worlds/gpt-5.4/basis_stall_risk_cautionary_moral_value_magic.py --goods buns --flaw stale
    python storyworlds/worlds/gpt-5.4/basis_stall_risk_cautionary_moral_value_magic.py --flaw cracked_pot
    python storyworlds/worlds/gpt-5.4/basis_stall_risk_cautionary_moral_value_magic.py --all
    python storyworlds/worlds/gpt-5.4/basis_stall_risk_cautionary_moral_value_magic.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/basis_stall_risk_cautionary_moral_value_magic.py --verify
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
PRIDE_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "honest", "steady", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    edible: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe", "vixen"}
        male = {"boy", "father", "buck", "fox", "badger", "crow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
class Goods:
    id: str
    label: str
    phrase: str
    plural: bool
    fresh_word: str
    flaw_text: dict[str, str]
    danger: dict[str, int]
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
class Flaw:
    id: str
    label: str
    visible: bool
    edible_risk: int
    line: str
    reveal: str
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
class Spell:
    id: str
    label: str
    phrase: str
    hides: set[str]
    show: str
    moral: str
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
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_sale_harms(world: World) -> list[str]:
    out: list[str] = []
    goods = world.get("goods")
    stall = world.get("stall")
    seller = world.get("seller")
    customer = world.get("customer")
    if goods.meters["sold"] < THRESHOLD or goods.meters["glamoured"] < THRESHOLD:
        return out
    sig = ("sale_harms",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    severity = int(goods.meters["severity"])
    stall.meters["trust_loss"] += severity
    seller.memes["shame"] += 1
    customer.memes["disappointment"] += 1
    if goods.meters["food_risk"] >= THRESHOLD:
        customer.meters["tummyache"] += 1
    out.append("__harm__")
    return out


def _r_low_trust_stalls(world: World) -> list[str]:
    out: list[str] = []
    stall = world.get("stall")
    if stall.meters["trust_loss"] < 2:
        return out
    sig = ("stalls",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stall.meters["empty"] += 1
    out.append("__empty__")
    return out


CAUSAL_RULES = [
    Rule(name="sale_harms", tag="social", apply=_r_sale_harms),
    Rule(name="low_trust_stalls", tag="social", apply=_r_low_trust_stalls),
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


def flaw_fits(goods: Goods, flaw: Flaw) -> bool:
    return flaw.id in goods.flaw_text


def spell_can_hide(spell: Spell, flaw: Flaw) -> bool:
    return flaw.id in spell.hides


def hazard_at_risk(goods: Goods, flaw: Flaw, spell: Spell) -> bool:
    return flaw_fits(goods, flaw) and spell_can_hide(spell, flaw)


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def flaw_severity(goods: Goods, flaw: Flaw, delay: int) -> int:
    return goods.danger.get(flaw.id, 1) + delay


def is_mended(remedy: Remedy, goods: Goods, flaw: Flaw, delay: int) -> bool:
    return remedy.power >= flaw_severity(goods, flaw, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, seller_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > seller_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if helper_older else 0.0)
    return helper_older and authority > PRIDE_INIT


def predict_harm(world: World) -> dict:
    sim = world.copy()
    _cast_spell(sim, narrate=False)
    _make_sale(sim, narrate=False)
    stall = sim.get("stall")
    customer = sim.get("customer")
    return {
        "trust_loss": stall.meters["trust_loss"],
        "tummyache": customer.meters["tummyache"],
        "empty": stall.meters["empty"],
    }


def introduce(world: World, seller: Entity, helper: Entity, elder: Entity, goods: Goods) -> None:
    species = seller.attrs.get("species", "rabbit")
    helper_species = helper.attrs.get("species", "sparrow")
    world.say(
        f"In a little market at the edge of the wood, {seller.id}, a young {species}, "
        f"helped {elder.label_word} at a neat {goods.label} stall. Beside {seller.id} "
        f"stood {helper.id}, a small {helper_species} with bright, watchful eyes."
    )
    world.say(
        f'Each morning {elder.label_word} said, "Honest scales and honest words are the '
        f'basis of a good stall." {seller.id} loved the praise that came when customers smiled.'
    )


def problem(world: World, seller: Entity, helper: Entity, goods: Goods, flaw: Flaw) -> None:
    world.say(
        f"But by noon, the tray held {goods.flaw_text[flaw.id]}. Few paws stopped, and the "
        f"small bell at the corner of the stall gave only a lonely clink."
    )
    world.say(
        f'{seller.id} looked at the quiet lane and whispered, "If no one buys these, our '
        f'stall will be the slowest one in the market."'
    )
    seller.memes["pride"] += 1
    seller.memes["worry"] += 1
    helper.memes["care"] += 1


def temptation(world: World, seller: Entity, spell: Spell) -> None:
    seller.memes["tempted"] += 1
    world.say(
        f"Then {seller.id} remembered {spell.phrase}. {spell.show} The poor goods suddenly "
        f"looked as fresh as morning dew."
    )


def warning(world: World, helper: Entity, seller: Entity, elder: Entity, flaw: Flaw) -> None:
    pred = predict_harm(world)
    world.facts["predicted_trust_loss"] = pred["trust_loss"]
    world.facts["predicted_tummyache"] = pred["tummyache"]
    world.facts["predicted_empty"] = pred["empty"]
    helper.memes["caution"] += 1
    extra = ""
    if pred["tummyache"] >= THRESHOLD:
        extra = " Someone could even feel sick after a bite."
    elif pred["empty"] >= THRESHOLD:
        extra = " If the trick is found out, the whole lane may turn away from our stall."
    world.say(
        f'{helper.id} fluttered close and said, "There is risk in that shine. It hides the truth, '
        f"and {elder.label_word} taught us better.{extra}\""
    )


def back_down(world: World, seller: Entity, helper: Entity, elder: Entity, goods: Goods) -> None:
    seller.memes["relief"] += 1
    helper.memes["relief"] += 1
    seller.memes["pride"] = 0.0
    world.say(
        f'{seller.id} looked at {helper.id}, who was older and steadier, and slowly let the '
        f"magic fade. Together they carried the tray behind the cloth curtain instead of selling "
        f"a single dishonest bite."
    )
    world.say(
        f'When {elder.label_word} returned, they told the truth at once. {elder.label_word.capitalize()} '
        f'nodded and said, "A small loss is lighter than a crooked gain."'
    )
    world.para()
    world.say(
        f"They baked a fresh little batch, and {seller.id} hung a hand-painted sign that read "
        f'"Fresh today, priced fairly." Soon the bell at the stall rang clean and bright, and '
        f'{seller.id} learned that patience could be as useful as magic.'
    )


def _cast_spell(world: World, narrate: bool = True) -> None:
    goods = world.get("goods")
    goods.meters["glamoured"] += 1
    if narrate:
        pass


def _make_sale(world: World, narrate: bool = True) -> None:
    goods = world.get("goods")
    goods.meters["sold"] += 1
    propagate(world, narrate=narrate)


def defy(world: World, seller: Entity) -> None:
    seller.memes["defiance"] += 1
    world.say(
        f'{seller.id} lifted {seller.pronoun("possessive")} chin. "Only for one customer," '
        f"{seller.pronoun()} said, and left the false shine in place."
    )


def sale(world: World, seller: Entity, customer: Entity, goods: Goods, flaw: Flaw) -> None:
    _cast_spell(world, narrate=False)
    _make_sale(world, narrate=False)
    effect = flaw.reveal
    world.say(
        f"Soon a traveler named {customer.id} bought {goods.phrase}. But when the traveler bit in, "
        f"{effect}."
    )
    if customer.meters["tummyache"] >= THRESHOLD:
        world.say(
            f"{customer.id} pressed a paw to {customer.pronoun('possessive')} middle and looked hurt."
        )
    else:
        world.say(
            f"{customer.id}'s face fell, and the bright market chatter thinned around the stall."
        )


def consequence(world: World, seller: Entity, helper: Entity) -> None:
    stall = world.get("stall")
    if stall.meters["empty"] >= THRESHOLD:
        world.say(
            f"Whispers hurried from basket to basket. Before long, customers passed by with careful eyes, "
            f"and the once-cheerful stall grew still."
        )
    else:
        world.say(
            f"The bell did not ring again right away. {seller.id} felt shame prick more sharply than hunger, "
            f"and even {helper.id} lowered {helper.pronoun('possessive')} head."
        )


def repair(world: World, elder: Entity, remedy: Remedy, goods: Goods, flaw: Flaw) -> None:
    stall = world.get("stall")
    goods_ent = world.get("goods")
    goods_ent.meters["glamoured"] = 0.0
    goods_ent.meters["sold"] = 0.0
    stall.meters["trust_loss"] = max(0.0, stall.meters["trust_loss"] - remedy.power)
    body = remedy.text.replace("{goods}", goods.label).replace("{flaw}", flaw.label)
    world.say(
        f"{elder.label_word.capitalize()} came back, listened once, and {body}."
    )


def repair_fail(world: World, elder: Entity, remedy: Remedy, goods: Goods, flaw: Flaw) -> None:
    body = remedy.fail.replace("{goods}", goods.label).replace("{flaw}", flaw.label)
    world.say(
        f"{elder.label_word.capitalize()} hurried back and {body}."
    )


def moral_happy(world: World, elder: Entity, seller: Entity, goods: Goods, spell: Spell) -> None:
    seller.memes["lesson"] += 1
    seller.memes["hope"] += 1
    world.say(
        f'Then {elder.label_word} touched the lantern with a harmless spark and said, "{spell.moral}, '
        f'not to hide wrong but to light the right path."'
    )
    world.say(
        f"{seller.id} helped mix a fresh bowl and served it plainly. By sunset the stall was busy again, "
        f"not because the goods glittered, but because the truth did."
    )
    world.say(
        f"From that day on, {seller.id} remembered that trust was the basis of the little stall, "
        f"and no shortcut was worth the risk of breaking it."
    )


def moral_grim(world: World, elder: Entity, seller: Entity, spell: Spell) -> None:
    seller.memes["lesson"] += 1
    world.say(
        f'{elder.label_word.capitalize()} folded the cloth over the empty counter and said, "A lie with '
        f'magic is still a lie." The market lamps glimmered, but none of their light could warm the silent stall.'
    )
    world.say(
        f"{seller.id} walked home carrying the unsold tray and a heavy heart. After that day, "
        f"{seller.pronoun()} never forgot that trust, once scattered, is hard to gather again."
    )
    world.say(
        f"The old spark was kept only for lighting lamps, and its shining became a reminder that power "
        f"must bow to honesty."
    )


def tell(
    goods: Goods,
    flaw: Flaw,
    spell: Spell,
    remedy: Remedy,
    seller_name: str = "Nia",
    seller_gender: str = "girl",
    seller_species: str = "rabbit",
    helper_name: str = "Tavi",
    helper_gender: str = "boy",
    helper_species: str = "sparrow",
    elder_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    seller_age: int = 5,
    helper_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    seller = world.add(
        Entity(
            id=seller_name,
            kind="character",
            type=seller_gender,
            role="seller",
            age=seller_age,
            attrs={"species": seller_species, "relation": relation},
            traits=["hopeful"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            age=helper_age,
            attrs={"species": helper_species, "relation": relation},
            traits=[trait],
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    customer = world.add(
        Entity(
            id="Bran",
            kind="character",
            type="badger",
            role="customer",
            attrs={"species": "badger"},
        )
    )
    stall = world.add(
        Entity(
            id="stall",
            kind="thing",
            type="stall",
            label="stall",
        )
    )
    goods_ent = world.add(
        Entity(
            id="goods",
            kind="thing",
            type="goods",
            label=goods.label,
            edible=True,
        )
    )
    charm = world.add(
        Entity(
            id="spell",
            kind="thing",
            type="spell",
            label=spell.label,
            magical=True,
        )
    )

    seller.memes["pride"] = PRIDE_INIT
    helper.memes["caution"] = initial_caution(trait)
    goods_ent.meters["severity"] = float(flaw_severity(goods, flaw, delay))
    goods_ent.meters["food_risk"] = float(1 if flaw.edible_risk else 0)
    world.facts["basis_line"] = "Honest scales and honest words are the basis of a good stall."
    world.facts["risk_word"] = "risk"

    introduce(world, seller, helper, elder, goods)
    problem(world, seller, helper, goods, flaw)

    world.para()
    temptation(world, seller, spell)
    warning(world, helper, seller, elder, flaw)

    averted = would_avert(relation, seller_age, helper_age, trait)
    if averted:
        back_down(world, seller, helper, elder, goods)
        outcome = "averted"
        mended = True
    else:
        defy(world, seller)
        world.para()
        sale(world, seller, customer, goods, flaw)
        consequence(world, seller, helper)
        world.para()
        mended = is_mended(remedy, goods, flaw, delay)
        if mended:
            repair(world, elder, remedy, goods, flaw)
            moral_happy(world, elder, seller, goods, spell)
            outcome = "mended"
        else:
            repair_fail(world, elder, remedy, goods, flaw)
            moral_grim(world, elder, seller, spell)
            outcome = "ruined"

    world.facts.update(
        seller=seller,
        helper=helper,
        elder=elder,
        customer=customer,
        goods_cfg=goods,
        flaw_cfg=flaw,
        spell_cfg=spell,
        remedy=remedy,
        outcome=outcome,
        averted=averted,
        mended=mended,
        relation=relation,
        delay=delay,
        trust_loss=world.get("stall").meters["trust_loss"],
        tummyache=world.get("customer").meters["tummyache"],
        empty=world.get("stall").meters["empty"],
        used_magic=world.get("goods").meters["glamoured"] >= THRESHOLD,
        lesson=seller.memes["lesson"] >= THRESHOLD,
        spell_entity=charm,
    )
    return world


GOODS = {
    "buns": Goods(
        id="buns",
        label="honey buns",
        phrase="a honey bun",
        plural=False,
        fresh_word="warm and soft",
        flaw_text={
            "stale": "honey buns gone dry around the edges",
            "sour": "honey buns brushed with cream that had begun to turn",
        },
        danger={"stale": 1, "sour": 2},
        tags={"buns", "market"},
    ),
    "tarts": Goods(
        id="tarts",
        label="berry tarts",
        phrase="a berry tart",
        plural=False,
        fresh_word="bright and sweet",
        flaw_text={
            "bruised": "berry tarts with sunken fruit on top",
            "stale": "berry tarts whose crusts had gone a little tough",
        },
        danger={"bruised": 1, "stale": 1},
        tags={"tarts", "market"},
    ),
    "tea": Goods(
        id="tea",
        label="mint tea",
        phrase="a cup of mint tea",
        plural=False,
        fresh_word="clear and fragrant",
        flaw_text={
            "weak": "mint tea watered down past kindness",
            "sour": "mint tea poured from milk that had turned",
        },
        danger={"weak": 1, "sour": 2},
        tags={"tea", "market"},
    ),
}

FLAWS = {
    "stale": Flaw(
        id="stale",
        label="staleness",
        visible=True,
        edible_risk=0,
        line="The crust had lost its kindness.",
        reveal="the false shine slipped, and the mouthful proved dry and old",
        tags={"food", "honesty"},
    ),
    "bruised": Flaw(
        id="bruised",
        label="bruises",
        visible=True,
        edible_risk=0,
        line="The fruit looked tired where it had been pressed.",
        reveal="the glossy berries sagged back into their bruised shapes",
        tags={"food", "honesty"},
    ),
    "weak": Flaw(
        id="weak",
        label="watered tea",
        visible=False,
        edible_risk=0,
        line="The smell was kind, but the flavor was thin.",
        reveal="the sparkle vanished from the cup, and the tea tasted thin as warm water",
        tags={"tea", "honesty"},
    ),
    "sour": Flaw(
        id="sour",
        label="sour milk",
        visible=False,
        edible_risk=1,
        line="A sharp smell hid beneath the sweet steam.",
        reveal="the sweet smell turned sharp, and the bite tasted wrong at once",
        tags={"food", "health"},
    ),
    "cracked_pot": Flaw(
        id="cracked_pot",
        label="a cracked pot",
        visible=True,
        edible_risk=0,
        line="The serving pot itself had a long crack in it.",
        reveal="the crack showed through the shine",
        tags={"pot"},
    ),
}

SPELLS = {
    "glamour": Spell(
        id="glamour",
        label="glamour charm",
        phrase="a glamour charm wrapped in blue thread",
        hides={"stale", "bruised"},
        show="A cool blue shimmer slid over the tray",
        moral="Magic should serve truth",
        tags={"magic", "glamour"},
    ),
    "moonmist": Spell(
        id="moonmist",
        label="moonmist dust",
        phrase="a pinch of moonmist dust in a paper twist",
        hides={"stale", "bruised", "weak"},
        show="Silver mist curled over the food like tiny moonbeams",
        moral="A bright trick is no excuse for a dark choice",
        tags={"magic", "glamour"},
    ),
    "golden_echo": Spell(
        id="golden_echo",
        label="golden echo",
        phrase="a golden echo rune on the underside of the tray",
        hides={"weak", "sour"},
        show="A honey-colored glimmer trembled around the cups and steam",
        moral="Power is safest in honest hands",
        tags={"magic", "glamour"},
    ),
}

REMEDIES = {
    "apology_fresh_batch": Remedy(
        id="apology_fresh_batch",
        sense=3,
        power=4,
        text="threw out the spoiled {goods}, apologized to every waiting customer, returned the coin, and set a fresh batch to warm",
        fail="apologized and returned one coin, but too many customers had already heard what happened",
        qa_text="apologized, returned the coin, and made a fresh batch",
        tags={"apology", "fresh_food"},
    ),
    "refund_sign": Remedy(
        id="refund_sign",
        sense=3,
        power=3,
        text='returned the coin, cleared the counter, and hung a sign that said "Not for sale until fresh"',
        fail='hung an honest sign and offered refunds, but the whisper had already run faster than the truth',
        qa_text='returned the coin and hung an honest sign',
        tags={"apology", "sign"},
    ),
    "discount": Remedy(
        id="discount",
        sense=1,
        power=1,
        text="offered the rest of the {goods} for half price",
        fail="tried to make up for it with cheap prices, which only made the market distrust the stall more",
        qa_text="offered cheap prices",
        tags={"cheap_price"},
    ),
}


GIRL_NAMES = ["Nia", "Mira", "Poppy", "Lena", "Wren", "Iris", "Faye", "Moss"]
BOY_NAMES = ["Tavi", "Bram", "Otis", "Ren", "Pip", "Rowan", "Ash", "Kip"]
SELLER_SPECIES = ["rabbit", "fox", "mouse", "hedgehog"]
HELPER_SPECIES = ["sparrow", "crow", "squirrel", "mouse"]
TRAITS = ["careful", "honest", "steady", "wise", "curious", "hopeful"]


@dataclass
class StoryParams:
    goods: str
    flaw: str
    spell: str
    remedy: str
    seller: str
    seller_gender: str
    seller_species: str
    helper: str
    helper_gender: str
    helper_species: str
    elder: str
    trait: str
    delay: int = 0
    seller_age: int = 5
    helper_age: int = 7
    relation: str = "siblings"
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
    "market": [
        (
            "What is a market stall?",
            "A market stall is a small stand where people sell things like food or cloth. It depends on customers trusting the seller."
        )
    ],
    "magic": [
        (
            "What is a glamour spell?",
            "A glamour spell is magic that changes how something looks. It can be harmless for a show, but it is wrong if it hides the truth."
        )
    ],
    "honesty": [
        (
            "Why is honesty important when selling things?",
            "Honesty helps people know what they are buying. Trust grows when sellers tell the truth and fades when they trick others."
        )
    ],
    "food": [
        (
            "Why should you not sell bad food?",
            "Bad food can disappoint people, and sometimes it can make them sick. Sellers should only offer food that is safe and good."
        )
    ],
    "apology": [
        (
            "Why does an honest apology help after a mistake?",
            "An honest apology shows that someone admits the harm and wants to mend it. It cannot erase the mistake, but it can start rebuilding trust."
        )
    ],
    "sign": [
        (
            "Why can a clear sign be helpful at a stall?",
            "A clear sign tells customers the truth right away. That helps everyone understand what is fresh and what is not for sale."
        )
    ],
}
KNOWLEDGE_ORDER = ["market", "magic", "honesty", "food", "apology", "sign"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_remedies():
        return combos
    for goods_id, goods in GOODS.items():
        for flaw_id, flaw in FLAWS.items():
            for spell_id, spell in SPELLS.items():
                if hazard_at_risk(goods, flaw, spell):
                    combos.append((goods_id, flaw_id, spell_id))
    return combos


def explain_rejection(goods: Goods, flaw: Flaw, spell: Spell) -> str:
    if not flaw_fits(goods, flaw):
        return (
            f"(No story: {goods.label} do not reasonably suffer from {flaw.label} here, "
            f"so the problem does not fit the stall.)"
        )
    if not spell_can_hide(spell, flaw):
        return (
            f"(No story: {spell.label} cannot honestly cover up {flaw.label}, so there is no deceptive magic risk to model.)"
        )
    return "(No story: this combination has no plausible deceptive risk.)"


def explain_remedy(rid: str) -> str:
    remedy = REMEDIES[rid]
    better = " / ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{rid}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.seller_age, params.helper_age, params.trait):
        return "averted"
    return "mended" if is_mended(REMEDIES[params.remedy], GOODS[params.goods], FLAWS[params.flaw], params.delay) else "ruined"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seller = f["seller"]
    helper = f["helper"]
    goods = f["goods_cfg"]
    flaw = f["flaw_cfg"]
    spell = f["spell_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short fable for a 3-to-5-year-old that includes the words "basis", "stall", and "risk", where a young seller is tempted to use magic at a market stall but a wiser helper stops the trick before any sale is made.',
            f"Tell a cautionary animal fable where {seller.id} wants to hide {flaw.label} in some {goods.label} with {spell.label}, but {helper.id} warns about the risk and helps choose honesty instead.",
            f'Write a moral fable in which a child learns that trust is the basis of trade, and magic should never be used to hide the truth.'
        ]
    if outcome == "ruined":
        return [
            f'Write a cautionary fable that includes the words "basis", "stall", and "risk", where magic is used to hide a problem at a market stall and the stall loses trust.',
            f"Tell a moral animal story where {seller.id} hides {flaw.label} with {spell.label}, harms the stall's good name, and learns too late that honesty is the basis of every fair bargain.",
            f"Write a small magic fable with a sad ending in which one dishonest sale empties a once-busy stall."
        ]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "basis", "stall", and "risk", where a young market seller uses magic badly, tells the truth afterward, and helps mend the harm.',
        f"Tell a gentle cautionary story where {seller.id} hides {flaw.label} in some {goods.label} with {spell.label}, then an elder repairs the mistake with honesty.",
        f"Write a moral fable in which magic tempts a child toward deception, but an apology and fresh work restore trust."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seller = f["seller"]
    helper = f["helper"]
    elder = f["elder"]
    customer = f["customer"]
    goods = f["goods_cfg"]
    flaw = f["flaw_cfg"]
    spell = f["spell_cfg"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seller.id}, a young {seller.attrs.get('species')}, {helper.id}, a watchful {helper.attrs.get('species')}, and {elder.label_word}, who helps run the market stall."
        ),
        (
            "What was the problem at the stall?",
            f"The stall still had {goods.flaw_text[flaw.id]}. That made {seller.id} worry that no one would buy from the stall."
        ),
        (
            f"Why did {helper.id} warn that the spell was a risk?",
            (
                f"{helper.id} warned that the magic would hide the truth instead of fixing it. "
                + (
                    "The helper could see that a customer might even feel sick."
                    if f.get("predicted_tummyache", 0) >= THRESHOLD
                    else "The helper knew that if the trick was found out, people would stop trusting the stall."
                )
            )
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {seller.id} do after the warning?",
                f"{seller.id} let the spell fade and told the truth to {elder.label_word}. Then they baked a fresh batch instead of selling the bad food."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the bell ringing cleanly at the stall and fresh food on the tray. The ending shows that honesty brought customers back without any trick."
            )
        )
    elif outcome == "mended":
        qa.append(
            (
                f"What happened to {customer.id} after buying the food?",
                (
                    f"{customer.id} discovered the hidden problem when the magic wore off. "
                    + (
                        f"{customer.pronoun('subject').capitalize()} even felt unwell after the bite."
                        if f["tummyache"] >= THRESHOLD
                        else "The traveler felt disappointed and hurt."
                    )
                )
            )
        )
        qa.append(
            (
                f"How did {elder.label_word} try to mend the harm?",
                f"{elder.label_word.capitalize()} {remedy.qa_text}. That honest action mattered because it faced the wrong directly instead of covering it again."
            )
        )
        qa.append(
            (
                "What moral did the seller learn?",
                f"{seller.id} learned that trust is the basis of the stall, and a shining trick is not worth the risk of breaking that trust. The story ends with truth, not glamour, drawing people back."
            )
        )
    else:
        qa.append(
            (
                "Why did the stall lose its good name?",
                f"It lost trust because the magic made bad goods look good long enough to trick a customer. When the trick was seen, whispers spread faster than the seller could explain."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the stall quiet and covered, and {seller.id} walking home ashamed. That sad ending proves that dishonest magic can spoil more than one sale."
            )
        )
        qa.append(
            (
                "What moral did the seller learn?",
                f"{seller.id} learned that power must bow to honesty. Once trust is broken, it is much harder to mend than a tray of food."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"market", "magic", "honesty"}
    if f["flaw_cfg"].edible_risk:
        tags.add("food")
    if f["outcome"] == "mended":
        tags |= set(f["remedy"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("edible", ent.edible), ("magical", ent.magical)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        goods="buns",
        flaw="stale",
        spell="glamour",
        remedy="apology_fresh_batch",
        seller="Nia",
        seller_gender="girl",
        seller_species="rabbit",
        helper="Tavi",
        helper_gender="boy",
        helper_species="sparrow",
        elder="mother",
        trait="careful",
        delay=0,
        seller_age=5,
        helper_age=7,
        relation="siblings",
    ),
    StoryParams(
        goods="tea",
        flaw="weak",
        spell="moonmist",
        remedy="refund_sign",
        seller="Bram",
        seller_gender="boy",
        seller_species="fox",
        helper="Mira",
        helper_gender="girl",
        helper_species="crow",
        elder="father",
        trait="steady",
        delay=0,
        seller_age=6,
        helper_age=5,
        relation="friends",
    ),
    StoryParams(
        goods="buns",
        flaw="sour",
        spell="golden_echo",
        remedy="refund_sign",
        seller="Poppy",
        seller_gender="girl",
        seller_species="mouse",
        helper="Ash",
        helper_gender="boy",
        helper_species="squirrel",
        elder="mother",
        trait="honest",
        delay=1,
        seller_age=6,
        helper_age=4,
        relation="siblings",
    ),
    StoryParams(
        goods="tarts",
        flaw="bruised",
        spell="glamour",
        remedy="apology_fresh_batch",
        seller="Ren",
        seller_gender="boy",
        seller_species="hedgehog",
        helper="Iris",
        helper_gender="girl",
        helper_species="sparrow",
        elder="father",
        trait="wise",
        delay=0,
        seller_age=5,
        helper_age=8,
        relation="siblings",
    ),
]


ASP_RULES = r"""
hazard(G,F,S) :- goods(G), flaw(F), spell(S), suffers(G,F), hides(S,F).
sensible(R) :- remedy(R), sense(R,N), sense_min(M), N >= M.
valid(G,F,S) :- goods(G), flaw(F), spell(S), hazard(G,F,S).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
helper_older :- relation(siblings), seller_age(SA), helper_age(HA), HA > SA.
bonus(4) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), pride_init(P), A > P.

severity(Dg + D) :- chosen_goods(G), chosen_flaw(F), danger(G,F,Dg), delay(D).
remedy_power(P) :- chosen_remedy(R), power(R,P).
mended :- remedy_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(mended) :- not averted, mended.
outcome(ruined) :- not averted, not mended.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid, goods in GOODS.items():
        lines.append(asp.fact("goods", gid))
        for flaw_id in sorted(goods.flaw_text):
            lines.append(asp.fact("suffers", gid, flaw_id))
            lines.append(asp.fact("danger", gid, flaw_id, goods.danger[flaw_id]))
    for fid in FLAWS:
        lines.append(asp.fact("flaw", fid))
    for sid, spell in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        for flaw_id in sorted(spell.hides):
            lines.append(asp.fact("hides", sid, flaw_id))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, remedy.sense))
        lines.append(asp.fact("power", rid, remedy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("pride_init", int(PRIDE_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_goods", params.goods),
            asp.fact("chosen_flaw", params.flaw),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("seller_age", params.seller_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magical market stall, a dishonest shortcut, and the cost of lost trust."
    )
    ap.add_argument("--goods", choices=GOODS)
    ap.add_argument("--flaw", choices=FLAWS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the harm spreads before the elder mends it")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goods and args.flaw and args.spell:
        goods = GOODS[args.goods]
        flaw = FLAWS[args.flaw]
        spell = SPELLS[args.spell]
        if not hazard_at_risk(goods, flaw, spell):
            raise StoryError(explain_rejection(goods, flaw, spell))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.goods is None or combo[0] == args.goods)
        and (args.flaw is None or combo[1] == args.flaw)
        and (args.spell is None or combo[2] == args.spell)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goods_id, flaw_id, spell_id = rng.choice(sorted(combos))
    remedy_id = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    seller_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    seller = _pick_name(rng, seller_gender)
    helper = _pick_name(rng, helper_gender, avoid=seller)
    seller_species = rng.choice(SELLER_SPECIES)
    helper_species = rng.choice(HELPER_SPECIES)
    elder = args.elder or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    seller_age, helper_age = rng.sample([4, 5, 6, 7, 8], 2)

    return StoryParams(
        goods=goods_id,
        flaw=flaw_id,
        spell=spell_id,
        remedy=remedy_id,
        seller=seller,
        seller_gender=seller_gender,
        seller_species=seller_species,
        helper=helper,
        helper_gender=helper_gender,
        helper_species=helper_species,
        elder=elder,
        trait=trait,
        delay=delay,
        seller_age=seller_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        goods = GOODS[params.goods]
        flaw = FLAWS[params.flaw]
        spell = SPELLS[params.spell]
        remedy = REMEDIES[params.remedy]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]})") from None

    if not hazard_at_risk(goods, flaw, spell):
        raise StoryError(explain_rejection(goods, flaw, spell))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_remedy(params.remedy))

    world = tell(
        goods=goods,
        flaw=flaw,
        spell=spell,
        remedy=remedy,
        seller_name=params.seller,
        seller_gender=params.seller_gender,
        seller_species=params.seller_species,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        helper_species=params.helper_species,
        elder_type=params.elder,
        trait=params.trait,
        delay=params.delay,
        seller_age=params.seller_age,
        helper_age=params.helper_age,
        relation=params.relation,
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_remedies()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible remedies match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(150):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (goods, flaw, spell) combos:\n")
        for goods_id, flaw_id, spell_id in combos:
            print(f"  {goods_id:8} {flaw_id:10} {spell_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.seller}: {p.goods} with {p.flaw} ({p.spell}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
