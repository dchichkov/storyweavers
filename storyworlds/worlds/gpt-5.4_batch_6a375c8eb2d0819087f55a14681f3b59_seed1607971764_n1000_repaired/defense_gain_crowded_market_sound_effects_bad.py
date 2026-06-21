#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/defense_gain_crowded_market_sound_effects_bad.py
============================================================================

A standalone story world for a fable-like tale set in a crowded market.

Premise
-------
A small market seller hears of a chance for quick gain and thinks of stepping
away from the stall. A wiser helper urges some defense first. If the stall is
left poorly guarded in the noisy crowd, a thief slips in, and the ending turns
bad. If the defense fits the goods and the crowd, the seller learns to value
care over quick gain.

The world model is built around:
- typed entities with physical meters and emotional memes
- a reasonableness gate for which defenses honestly protect which goods
- a simple outcome model: crowd pressure versus the chosen defense
- fable-like prose with foreshadowing and concrete sound effects

Run it
------
    python storyworlds/worlds/gpt-5.4/defense_gain_crowded_market_sound_effects_bad.py
    python storyworlds/worlds/gpt-5.4/defense_gain_crowded_market_sound_effects_bad.py --goods coin_pot --defense lockbox
    python storyworlds/worlds/gpt-5.4/defense_gain_crowded_market_sound_effects_bad.py --goods melon_stack --defense lockbox
    python storyworlds/worlds/gpt-5.4/defense_gain_crowded_market_sound_effects_bad.py --all
    python storyworlds/worlds/gpt-5.4/defense_gain_crowded_market_sound_effects_bad.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/defense_gain_crowded_market_sound_effects_bad.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    coin_like: bool = False
    # typed state axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goat_female", "girl", "mother", "woman"}
        male = {"fox", "goat_male", "boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    risk: str
    portability: int
    shine: str
    sound: str
    moral_loss: str
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
class Crowd:
    id: str
    label: str
    soundscape: str
    density: int
    dust: str
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
class Lure:
    id: str
    offer: str
    seller: str
    cry: str
    promise: str
    distance: int
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
class DefensePlan:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers_portability: int
    sense: int
    text: str
    qa_text: str
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
class HeroSpec:
    id: str
    type: str
    virtue: str
    flaw: str
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


def _r_open_stall(world: World) -> list[str]:
    hero = world.get("hero")
    stall = world.get("stall")
    goods = world.get("goods")
    if hero.attrs.get("away") and stall.meters["guarded"] < THRESHOLD:
        sig = ("open_stall",)
        if sig not in world.fired:
            world.fired.add(sig)
            stall.meters["risk"] += 1
            goods.meters["exposed"] += 1
    return []


def _r_crowd_pressure(world: World) -> list[str]:
    stall = world.get("stall")
    crowd = world.get("crowd")
    if stall.meters["risk"] < THRESHOLD:
        return []
    sig = ("crowd_pressure",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stall.meters["pressure"] += crowd.attrs["density"]
    return []


def _r_theft(world: World) -> list[str]:
    stall = world.get("stall")
    goods = world.get("goods")
    thief = world.get("thief")
    hero = world.get("hero")
    helper = world.get("helper")
    if stall.meters["pressure"] < THRESHOLD:
        return []
    if goods.meters["safe"] >= THRESHOLD:
        return []
    sig = ("theft",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    goods.meters["stolen"] += 1
    hero.memes["shock"] += 1
    hero.memes["regret"] += 1
    helper.memes["sorrow"] += 1
    thief.meters["loot"] += 1
    return ["__stolen__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="open_stall", tag="physical", apply=_r_open_stall),
    Rule(name="crowd_pressure", tag="physical", apply=_r_crowd_pressure),
    Rule(name="theft", tag="social", apply=_r_theft),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
            else:
                continue
        snapshot = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        changed = changed or len(world.fired) > snapshot
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def defense_fits(goods: Goods, defense: DefensePlan) -> bool:
    return goods.risk in defense.guards and goods.portability <= defense.covers_portability


def sensible_defenses() -> list[DefensePlan]:
    return [d for d in DEFENSES.values() if d.sense >= SENSE_MIN]


def risk_level(crowd: Crowd, lure: Lure) -> int:
    return crowd.density + lure.distance


def can_hold(defense: DefensePlan, crowd: Crowd, lure: Lure) -> bool:
    return defense.covers_portability >= risk_level(crowd, lure)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for hero in HEROES:
        for goods_id, goods in GOODS.items():
            for crowd_id, crowd in CROWDS.items():
                for lure_id, lure in LURES.items():
                    if any(defense_fits(goods, d) for d in sensible_defenses()):
                        combos.append((hero, goods_id, crowd_id, lure_id))
    return combos


@dataclass
class StoryParams:
    hero: str
    goods: str
    crowd: str
    lure: str
    defense: str
    helper_name: str
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


def foreshadow_line(world: World, hero: Entity, helper: Entity, goods: Goods, crowd: Crowd) -> None:
    world.say(
        f"In the crowded market, {crowd.soundscape}. {hero.id} kept a stall of {goods.phrase}, "
        f"and the {goods.sound} sounded sweet to greedy ears."
    )
    world.say(
        f"{helper.id}, who shared the next mat, watched the tide of elbows and baskets and said, "
        f'"A stall without defense in such a press is like a nest with no rim."'
    )


def setup_market(world: World, hero: Entity, helper: Entity, goods: Goods, crowd: Crowd) -> None:
    hero.memes["hope"] += 1
    hero.memes["pride"] += 1
    stall = world.add(Entity(id="stall", type="stall", label="stall"))
    crowd_ent = world.add(Entity(id="crowd", type="crowd", label=crowd.label, attrs={"density": crowd.density}))
    goods_ent = world.add(
        Entity(
            id="goods",
            type="goods",
            label=goods.label,
            portable=True,
            coin_like=goods.risk == "coin",
        )
    )
    thief = world.add(Entity(id="thief", kind="character", type="fox", label="a sly fox", role="thief"))
    stall.meters["guarded"] = 0.0
    goods_ent.meters["safe"] = 0.0
    goods_ent.meters["stolen"] = 0.0
    world.facts["crowd_cfg"] = crowd
    world.facts["goods_cfg"] = goods
    world.facts["thief"] = thief
    foreshadow_line(world, hero, helper, goods, crowd)
    world.say(
        f"{hero.id} had come early hoping to gain a little more than yesterday, "
        f"for the season had been lean and every copper mattered."
    )


def cry_of_gain(world: World, hero: Entity, lure: Lure) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"Then across the lane came a cry — {lure.cry}! It rang through the market like a brass spoon on a bowl."
    )
    world.say(
        f'A peddler of {lure.seller} called, "{lure.promise}" and {hero.id} felt the word "gain" tug at {hero.pronoun("possessive")} thoughts.'
    )


def helper_warns(world: World, helper: Entity, hero: Entity, defense: DefensePlan, goods: Goods, crowd: Crowd, lure: Lure) -> None:
    pred = predict_loss(world, defense)
    world.facts["predicted_loss"] = pred["stolen"]
    helper.memes["care"] += 1
    if pred["stolen"]:
        extra = " A fast paw will always thank a foolish back."
    else:
        extra = " A good knot is slower than regret, but wiser."
    world.say(
        f'{helper.id} flicked {helper.pronoun("possessive")} tail toward the stall. '
        f'"If you must chase that gain, leave some defense behind. {defense.label.capitalize()} will guard {goods.label} against this {crowd.label}."{extra}'
    )


def choose_defense(world: World, hero: Entity, defense: DefensePlan) -> None:
    stall = world.get("stall")
    goods = world.get("goods")
    hero.memes["resolve"] += 1
    stall.meters["guarded"] = 1.0
    world.say(defense.text)
    if can_hold(defense, world.get("crowd_cfg"), world.get("lure_cfg")):
        goods.meters["safe"] = 1.0


def hurry_away(world: World, hero: Entity, lure: Lure) -> None:
    hero.attrs["away"] = True
    hero.memes["greed"] += 1
    world.say(
        f'So off {hero.pronoun("subject")} hurried, pad-pad through the dust, following the voice about {lure.offer}. '
        f"The lane was long enough for worry and short enough for trouble."
    )


def theft_scene(world: World, goods: Goods, crowd: Crowd) -> None:
    world.say(
        f"Back at the stall the market went clatter-clatter, bump-bump, and rustle-rustle. "
        f"In that noisy press, a sly fox brushed past once, then twice, and then — snip! — the {goods.label} were gone."
    )
    world.say(
        f"When {world.get('hero').id} returned, only a wavering space remained where the {goods.label} had been, "
        f"and the dust of the {crowd.label} still danced over the loss."
    )


def safe_return(world: World, hero: Entity, helper: Entity, goods: Goods) -> None:
    hero.attrs["away"] = False
    hero.memes["relief"] += 1
    helper.memes["approval"] += 1
    world.say(
        f"When {hero.id} came back, the {goods.label} still waited where they should. "
        f"The little defense had earned no applause, but it had kept the day whole."
    )


def lesson_bad(world: World, hero: Entity, helper: Entity, goods: Goods) -> None:
    world.say(
        f'{helper.id} said softly, "You ran to gain one bright bargain and lost {goods.moral_loss} instead."'
    )
    world.say(
        f"{hero.id} bowed {hero.pronoun('possessive')} head. From that day on, {hero.pronoun('subject')} learned that a small defense is dearer than a greedy errand."
    )


def lesson_good(world: World, hero: Entity, helper: Entity, defense: DefensePlan) -> None:
    world.say(
        f'{helper.id} smiled and said, "There is gain in caution too, though it makes less noise."'
    )
    world.say(
        f"{hero.id} nodded and touched the {defense.label}. Ever after, {hero.pronoun('subject')} remembered that wise defense keeps honest profit from blowing away."
    )


def predict_loss(world: World, defense: DefensePlan) -> dict:
    sim = world.copy()
    sim.facts["crowd_cfg"] = world.facts["crowd_cfg"]
    sim.facts["lure_cfg"] = world.facts["lure_cfg"]
    sim.get("hero").attrs["away"] = True
    sim.get("stall").meters["guarded"] = 1.0
    if can_hold(defense, sim.facts["crowd_cfg"], sim.facts["lure_cfg"]):
        sim.get("goods").meters["safe"] = 1.0
    propagate(sim, narrate=False)
    return {"stolen": sim.get("goods").meters["stolen"] >= THRESHOLD}


def tell(hero_spec: HeroSpec, goods: Goods, crowd: Crowd, lure: Lure, defense: DefensePlan, helper_name: str) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_spec.id,
            kind="character",
            type=hero_spec.type,
            label=hero_spec.id,
            role="hero",
            traits=[hero_spec.virtue, hero_spec.flaw],
            attrs={"away": False},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type="hen",
            label=helper_name,
            role="helper",
            traits=["careful"],
            attrs={},
        )
    )

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["goods_cfg"] = goods
    world.facts["crowd_cfg"] = crowd
    world.facts["lure_cfg"] = lure
    world.facts["defense_cfg"] = defense

    setup_market(world, hero, helper, goods, crowd)

    world.para()
    cry_of_gain(world, hero, lure)
    helper_warns(world, helper, hero, defense, goods, crowd, lure)
    choose_defense(world, hero, defense)
    hurry_away(world, hero, lure)

    world.para()
    propagate(world, narrate=False)
    if world.get("goods").meters["stolen"] >= THRESHOLD:
        theft_scene(world, goods, crowd)
        world.para()
        lesson_bad(world, hero, helper, goods)
        outcome = "bad"
    else:
        safe_return(world, hero, helper, goods)
        world.para()
        lesson_good(world, hero, helper, defense)
        outcome = "good"

    world.facts["outcome"] = outcome
    world.facts["stolen"] = world.get("goods").meters["stolen"] >= THRESHOLD
    world.facts["risk_value"] = risk_level(crowd, lure)
    return world


GOODS = {
    "coin_pot": Goods(
        id="coin_pot",
        label="coin pot",
        phrase="a clay pot of copper coins",
        plural=False,
        risk="coin",
        portability=2,
        shine="The coins flashed whenever the sun found them.",
        sound="clink-clink",
        moral_loss="the morning's bread money",
        tags={"coins", "theft"},
    ),
    "spice_sacks": Goods(
        id="spice_sacks",
        label="spice sacks",
        phrase="three bright sacks of cinnamon and cumin",
        plural=True,
        risk="snatch",
        portability=2,
        shine="Red and gold powder glowed at the seams.",
        sound="swish-swish",
        moral_loss="the best spices in the stall",
        tags={"spice", "theft"},
    ),
    "melon_stack": Goods(
        id="melon_stack",
        label="melon stack",
        phrase="a neat stack of striped melons",
        plural=True,
        risk="bulk",
        portability=1,
        shine="Their green skins shone like polished stones.",
        sound="thump-thump",
        moral_loss="half the day's produce",
        tags={"fruit", "theft"},
    ),
}

CROWDS = {
    "noon_bustle": Crowd(
        id="noon_bustle",
        label="noon bustle",
        soundscape="patter of sandals, hawkers calling, and donkeys snorting",
        density=1,
        dust="light dust",
        tags={"market", "noise"},
    ),
    "morning_rush": Crowd(
        id="morning_rush",
        label="morning rush",
        soundscape="clatter of carts, baa-baa of goats, and copper clinking",
        density=2,
        dust="spinning dust",
        tags={"market", "noise"},
    ),
    "festival_press": Crowd(
        id="festival_press",
        label="festival press",
        soundscape="drums boom-boom, feet shuffle-shuffle, and traders shout over one another",
        density=3,
        dust="thick dust",
        tags={"market", "noise"},
    ),
}

LURES = {
    "cheap_pears": Lure(
        id="cheap_pears",
        offer="cheap pears",
        seller="pears",
        cry="Pears! Pears! Two for one!",
        promise="Come now, neighbor, buy quickly and sell dearly after",
        distance=1,
        tags={"bargain"},
    ),
    "rare_dye": Lure(
        id="rare_dye",
        offer="rare blue dye",
        seller="rare blue dye",
        cry="Blue dye! River-blue dye!",
        promise="A little jar here will bring you a fine gain by sunset",
        distance=2,
        tags={"bargain"},
    ),
    "dice_corner": Lure(
        id="dice_corner",
        offer="a wagering circle",
        seller="dice and bold promises",
        cry="Rattle-rattle! One toss for double!",
        promise="Why creep toward profit when luck can carry you there at one leap?",
        distance=2,
        tags={"gamble"},
    ),
}

DEFENSES = {
    "watch_hen": DefensePlan(
        id="watch_hen",
        label="watch-hen",
        phrase="a watchful neighbor",
        guards={"snatch", "bulk", "coin"},
        covers_portability=3,
        sense=3,
        text="Before leaving, the seller asked the neighbor hen to watch the mat and count every curious paw.",
        qa_text="asked the neighbor hen to watch the stall",
        tags={"helper", "defense"},
    ),
    "lockbox": DefensePlan(
        id="lockbox",
        label="lockbox",
        phrase="a small iron lockbox",
        guards={"coin"},
        covers_portability=3,
        sense=3,
        text="Before leaving, the seller tucked the coins into a small iron lockbox and slid it beneath the table.",
        qa_text="hid the coins in a lockbox under the stall",
        tags={"lockbox", "defense"},
    ),
    "rope_bell": DefensePlan(
        id="rope_bell",
        label="rope bell",
        phrase="a bell tied to a rope around the goods",
        guards={"snatch", "bulk"},
        covers_portability=1,
        sense=2,
        text="Before leaving, the seller looped a rope about the goods and tied on a little bell that would ring at the first tug.",
        qa_text="tied a rope and bell around the goods",
        tags={"bell", "defense"},
    ),
    "cloth_cover": DefensePlan(
        id="cloth_cover",
        label="cloth cover",
        phrase="a plain cloth thrown over the goods",
        guards={"snatch"},
        covers_portability=1,
        sense=1,
        text="Before leaving, the seller threw a plain cloth over the goods and hoped dullness would do the guarding.",
        qa_text="covered the goods with a plain cloth",
        tags={"cloth", "defense"},
    ),
}

HEROES = {
    "Nuri": HeroSpec(id="Nuri", type="goat_female", virtue="diligent", flaw="eager"),
    "Toma": HeroSpec(id="Toma", type="goat_male", virtue="hardworking", flaw="greedy"),
    "Sela": HeroSpec(id="Sela", type="hen", virtue="patient", flaw="restless"),
}

HELPER_NAMES = ["Mira", "Pip", "Lark", "Dina"]


def outcome_of(params: StoryParams) -> str:
    if params.goods not in GOODS or params.crowd not in CROWDS or params.lure not in LURES or params.defense not in DEFENSES:
        raise StoryError("(No story: unknown option in parameters.)")
    defense = DEFENSES[params.defense]
    goods = GOODS[params.goods]
    if not defense_fits(goods, defense):
        raise StoryError(explain_rejection(goods, defense))
    return "good" if can_hold(defense, CROWDS[params.crowd], LURES[params.lure]) else "bad"


KNOWLEDGE = {
    "market": [
        (
            "What is a market?",
            "A market is a place where many people gather to buy and sell goods. It can be noisy and crowded, so sellers must keep watch over their things.",
        )
    ],
    "theft": [
        (
            "Why is it easier for thieves to steal in a crowd?",
            "A crowd gives a thief cover because many feet, voices, and elbows are moving at once. Noise and confusion make it harder to notice one sly hand.",
        )
    ],
    "defense": [
        (
            "What does defense mean in a market story?",
            "Defense means the steps someone takes to protect goods from loss or harm. In a market, that can mean locking things up or asking a trusted neighbor to watch them.",
        )
    ],
    "gain": [
        (
            "What is gain?",
            "Gain is getting more than you had before, such as extra money or a better bargain. But chasing gain too fast can also bring loss.",
        )
    ],
    "bell": [
        (
            "Why would a bell help guard a stall?",
            "A bell makes a sound when someone tugs at the goods. That noise can warn the seller or a neighbor that something is being moved.",
        )
    ],
    "lockbox": [
        (
            "What is a lockbox?",
            "A lockbox is a small strong box that can be shut tight. People use it to keep coins or other valuable things safer.",
        )
    ],
    "helper": [
        (
            "Why can a helper be better than a clever object?",
            "A helper can see, think, and speak, while an object cannot. A watchful friend notices trouble that a rope or box might miss.",
        )
    ],
    "coins": [
        (
            "Why do coins tempt thieves?",
            "Coins are small, valuable, and easy to hide in a pocket or paw. That makes them tempting when no one is watching closely.",
        )
    ],
    "spice": [
        (
            "Why were spices precious in old markets?",
            "Spices were precious because they were useful, fragrant, and often brought from far away. A seller could lose a lot when even one sack went missing.",
        )
    ],
    "fruit": [
        (
            "Why are heavy melons harder to steal than coins?",
            "Heavy melons take more effort to carry and hide. Even in a crowd, large goods are harder to snatch quickly.",
        )
    ],
}
KNOWLEDGE_ORDER = ["market", "theft", "defense", "gain", "bell", "lockbox", "helper", "coins", "spice", "fruit"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goods = f["goods_cfg"]
    crowd = f["crowd_cfg"]
    lure = f["lure_cfg"]
    defense = f["defense_cfg"]
    outcome = f["outcome"]
    if outcome == "bad":
        return [
            f'Write a short fable for a young child set in a crowded market. Use the words "defense" and "gain," include sound effects, and end badly.',
            f"Tell a market fable where {hero.id} hears of {lure.offer}, leaves {goods.phrase} with only {defense.phrase}, and learns that weak defense can turn hoped-for gain into loss.",
            f"Write a cautionary animal story with foreshadowing, noisy market sounds, and a bad ending in which a seller chases quick gain and a thief steals the goods.",
        ]
    return [
        f'Write a short fable for a young child set in a crowded market. Use the words "defense" and "gain," include sound effects, and let caution save the day.',
        f"Tell a market fable where {hero.id} wants a quick gain, but {defense.phrase} protects {goods.phrase} while the seller is away.",
        f"Write an animal story with foreshadowing and market noises that teaches that wise defense can be a kind of gain.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    goods = f["goods_cfg"]
    crowd = f["crowd_cfg"]
    lure = f["lure_cfg"]
    defense = f["defense_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a market seller, and {helper.id}, the careful neighbor who offered advice. The story follows what happened when {hero.id} thought a quick gain mattered more than guarding the stall.",
        ),
        (
            "Where did the story happen?",
            f"It happened in a crowded market full of noise, carts, and shoppers. That busy place matters because the crowd made it easier for trouble to hide.",
        ),
        (
            f"What tempted {hero.id} to leave the stall?",
            f"{hero.id} heard a cry about {lure.offer} and hoped it might bring quick gain. The tempting call pulled {hero.pronoun('object')} away from careful thinking.",
        ),
        (
            f"What warning did {helper.id} give?",
            f"{helper.id} warned that a stall in such a crowd needed defense before {hero.id} went chasing profit. The warning was really about cause and effect: leave goods exposed in a noisy crowd, and a thief may notice first.",
        ),
    ]
    if outcome == "bad":
        qa.append(
            (
                "Why did the ending turn bad?",
                f"The ending turned bad because the stall was left with a defense too weak for the crowd and the distance of the errand. While {hero.id} was away, the press and noise covered the thief's movements, so the {goods.label} were stolen.",
            )
        )
        qa.append(
            (
                f"What was lost, and what lesson did {hero.id} learn?",
                f"{hero.id} lost {goods.moral_loss}. After that, {hero.pronoun('subject')} learned that chasing gain without good defense can cost more than it promises.",
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} protect the stall?",
                f"{hero.pronoun('subject').capitalize()} {defense.qa_text}. That defense matched both the kind of goods and the danger of the crowd, so the stall stayed safe while {hero.pronoun('subject')} was away.",
            )
        )
        qa.append(
            (
                "What is the lesson at the end?",
                f"The lesson is that wise defense is a kind of gain. By guarding the stall first, {hero.id} kept the whole day from turning into loss.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"market", "theft", "defense", "gain"}
    goods = world.facts["goods_cfg"]
    defense = world.facts["defense_cfg"]
    crowd = world.facts["crowd_cfg"]
    if "coins" in goods.tags:
        tags.add("coins")
    if "spice" in goods.tags:
        tags.add("spice")
    if "fruit" in goods.tags:
        tags.add("fruit")
    tags |= defense.tags
    tags |= crowd.tags
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
            shown = {k: v for k, v in e.attrs.items() if v or k == "away"}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="Nuri",
        goods="coin_pot",
        crowd="festival_press",
        lure="rare_dye",
        defense="lockbox",
        helper_name="Mira",
    ),
    StoryParams(
        hero="Toma",
        goods="spice_sacks",
        crowd="festival_press",
        lure="dice_corner",
        defense="rope_bell",
        helper_name="Pip",
    ),
    StoryParams(
        hero="Sela",
        goods="melon_stack",
        crowd="morning_rush",
        lure="cheap_pears",
        defense="rope_bell",
        helper_name="Lark",
    ),
    StoryParams(
        hero="Nuri",
        goods="spice_sacks",
        crowd="noon_bustle",
        lure="cheap_pears",
        defense="watch_hen",
        helper_name="Dina",
    ),
]


def explain_rejection(goods: Goods, defense: DefensePlan) -> str:
    if goods.risk not in defense.guards:
        return (
            f"(No story: {defense.label} does not honestly protect {goods.label}. "
            f"The defense and the kind of goods must match.)"
        )
    if goods.portability > defense.covers_portability:
        return (
            f"(No story: {defense.label} is too weak for goods as easy to carry as {goods.label}. "
            f"Pick a stronger defense.)"
        )
    if defense.sense < SENSE_MIN:
        return (
            f"(No story: {defense.label} is known, but it is too flimsy to be a sensible defense here.)"
        )
    return "(No story: this defense does not make sense for these goods.)"


ASP_RULES = r"""
% reasonable fit: the defense must match the goods and be sensible
fits(G,D) :- goods(G), defense(D), risk(G,R), guards(D,R), portability(G,P), cover(D,C), P <= C.
sensible(D) :- defense(D), sense(D,S), sense_min(M), S >= M.
valid(H,G,C,L) :- hero(H), goods(G), crowd(C), lure(L), fits(G,D), sensible(D).

% outcome model
risk_level(V) :- chosen_crowd(C), density(C,DC), chosen_lure(L), distance(L,DL), V = DC + DL.
good :- chosen_goods(G), chosen_defense(D), fits(G,D), sensible(D), risk_level(V), cover(D,C), C >= V.
bad :- chosen_goods(G), chosen_defense(D), fits(G,D), sensible(D), risk_level(V), cover(D,C), C < V.
outcome(good) :- good.
outcome(bad) :- bad.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for gid, goods in GOODS.items():
        lines.append(asp.fact("goods", gid))
        lines.append(asp.fact("risk", gid, goods.risk))
        lines.append(asp.fact("portability", gid, goods.portability))
    for cid, crowd in CROWDS.items():
        lines.append(asp.fact("crowd", cid))
        lines.append(asp.fact("density", cid, crowd.density))
    for lid, lure in LURES.items():
        lines.append(asp.fact("lure", lid))
        lines.append(asp.fact("distance", lid, lure.distance))
    for did, defense in DEFENSES.items():
        lines.append(asp.fact("defense", did))
        for guard in sorted(defense.guards):
            lines.append(asp.fact("guards", did, guard))
        lines.append(asp.fact("cover", did, defense.covers_portability))
        lines.append(asp.fact("sense", did, defense.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_goods", params.goods),
            asp.fact("chosen_defense", params.defense),
            asp.fact("chosen_crowd", params.crowd),
            asp.fact("chosen_lure", params.lure),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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

    c_sens = set(asp_sensible())
    p_sens = {d.id for d in sensible_defenses()}
    if c_sens == p_sens:
        print(f"OK: sensible defenses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible defenses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected failure resolving params for seed {s}.")
            break

    mismatches = 0
    for params in cases:
        try:
            py_out = outcome_of(params)
            asp_out = asp_outcome(params)
            if py_out != asp_out:
                mismatches += 1
        except StoryError as err:
            rc = 1
            print(f"Outcome check crashed for {params}: {err}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    # smoke test ordinary story generation and rendering
    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a crowded market, a tempting gain, and the need for defense."
    )
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--goods", choices=sorted(GOODS))
    ap.add_argument("--crowd", choices=sorted(CROWDS))
    ap.add_argument("--lure", choices=sorted(LURES))
    ap.add_argument("--defense", choices=sorted(DEFENSES))
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goods and args.defense:
        goods = GOODS[args.goods]
        defense = DEFENSES[args.defense]
        if defense.sense < SENSE_MIN or not defense_fits(goods, defense):
            raise StoryError(explain_rejection(goods, defense))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.goods is None or combo[1] == args.goods)
        and (args.crowd is None or combo[2] == args.crowd)
        and (args.lure is None or combo[3] == args.lure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, goods_id, crowd_id, lure_id = rng.choice(sorted(combos))
    candidate_defenses = [
        did
        for did, defense in DEFENSES.items()
        if defense.sense >= SENSE_MIN
        and defense_fits(GOODS[goods_id], defense)
        and (args.defense is None or did == args.defense)
    ]
    if not candidate_defenses:
        raise StoryError("(No sensible defense matches the chosen goods.)")
    defense_id = rng.choice(sorted(candidate_defenses))
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        hero=hero_id,
        goods=goods_id,
        crowd=crowd_id,
        lure=lure_id,
        defense=defense_id,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"(No story: unknown hero '{params.hero}'.)")
    if params.goods not in GOODS:
        raise StoryError(f"(No story: unknown goods '{params.goods}'.)")
    if params.crowd not in CROWDS:
        raise StoryError(f"(No story: unknown crowd '{params.crowd}'.)")
    if params.lure not in LURES:
        raise StoryError(f"(No story: unknown lure '{params.lure}'.)")
    if params.defense not in DEFENSES:
        raise StoryError(f"(No story: unknown defense '{params.defense}'.)")
    goods = GOODS[params.goods]
    defense = DEFENSES[params.defense]
    if defense.sense < SENSE_MIN or not defense_fits(goods, defense):
        raise StoryError(explain_rejection(goods, defense))

    world = tell(
        hero_spec=HEROES[params.hero],
        goods=goods,
        crowd=CROWDS[params.crowd],
        lure=LURES[params.lure],
        defense=defense,
        helper_name=params.helper_name,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible defenses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, goods, crowd, lure) combos:\n")
        for hero, goods, crowd, lure in combos:
            print(f"  {hero:6} {goods:12} {crowd:14} {lure}")
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
            header = f"### {p.hero}: {p.goods} in {p.crowd} with {p.defense} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
