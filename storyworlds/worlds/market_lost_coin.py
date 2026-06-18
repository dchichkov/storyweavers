#!/usr/bin/env python3
"""
storyworlds/worlds/market_lost_coin.py
======================================

Story world sketch for a market + lost-coin domain.

Reference story idea (market visit, warning, compromise):
-------------------------------------------------------
Once, there was a child at a bustling market with a few coins in a loose pocket.
The child wanted to run after bright things, but the parent warned the coins could
be lost in the crowd. Instead of the confrontation escalating, they found a safer
way to enjoy the market together.
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

# Make the shared result containers importable when this script is run directly
# (``python storyworlds/worlds/market_lost_coin.py``).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "thing"
    type: str = "object"          # boy, girl, mother, coin, gear, ...
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""              # for the object being carried / protected
    protective: bool = False      # true for gear that prevents loss
    covers: set[str] = field(default_factory=set)  # regions this item protects
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Market:
    id: str
    label: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str                   # "ran through the crowded stalls"
    gerund: str                 # "running through the crowded stalls"
    rush: str                   # "ran through the crowd"
    risk: str = "loss"          # risk class; we use this gate for coin loss
    zones: set[str] = field(default_factory=set)  # where the actor's body is exposed
    keyword: str = ""           # for generation prompts
    tags: set[str] = field(default_factory=set)


@dataclass
class Coin:
    id: str
    label: str
    phrase: str
    region: str                 # "pocket" in this world
    plural: bool = False


@dataclass
class Pouch:
    id: str
    label: str
    covers: set[str]            # regions it protects
    guards: set[str]            # risks it reduces
    offer: str                  # text for compromise line
    tail: str                   # closing line for resolution


@dataclass
class StoryParams:
    market: str
    activity: str
    coin: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, market: Market) -> None:
        self.market = market
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id and e.protective]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.market)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.zone = set(self.zone)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_coin_slips(world: World) -> list[str]:
    out: list[str] = []
    coin_id = world.facts.get("coin_id")
    if not coin_id or coin_id not in world.entities:
        return out
    coin = world.entities[coin_id]
    if coin.meters["lost"] >= THRESHOLD:
        return out

    owner = world.entities.get(coin.owner or "")
    if owner is None:
        return out
    if owner.meters["rush"] < THRESHOLD:
        return out
    if world.covered(owner, coin.region):
        return out

    sig = ("coin_slip", coin.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)

    coin.meters["lost"] += 1
    out.append(
        f"{owner.pronoun('possessive').capitalize()} {coin.label} slipped from {owner.pronoun('possessive')} "
        f"{coin.region} and rolled under a table near the fish stall."
    )
    return out


def _r_parent_trouble(world: World) -> list[str]:
    coin_id = world.facts.get("coin_id")
    if not coin_id:
        return []
    coin = world.entities.get(coin_id)
    parent_id = world.facts.get("parent")
    parent = world.entities.get(parent_id or "", None)
    if coin is None or parent is None or coin.meters["lost"] < THRESHOLD:
        return []
    sig = ("parent_trouble", "lost_coin")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parent.meters["stress"] += 1
    return ["The parent knelt down and helped search the crowded stones for it."]


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("coin_slips", "physical", _r_coin_slips),
    Rule("parent_trouble", "physical", _r_parent_trouble),
    Rule("conflict", "social", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for sent in sents:
                    if sent != "__conflict__":
                        produced.append(sent)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def prize_at_risk(activity: Activity, coin: Coin) -> bool:
    return coin.region in activity.zones


def select_gear(activity: Activity, coin: Coin) -> Optional[Pouch]:
    for pouch in GEAR:
        if activity.risk in pouch.guards and coin.region in pouch.covers:
            return pouch
    return None


def predict_loss(world: World, actor: Entity, activity: Activity) -> dict[str, bool]:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    coin_id = sim.facts.get("coin_id")
    coin = sim.entities.get(coin_id, None)
    lost = coin is not None and coin.meters["lost"] >= THRESHOLD
    return {"lost": lost}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.market.affords:
        return
    world.zone = set(activity.zones)
    actor.meters[activity.risk] += 1
    actor.meters["rush"] += 1
    actor.memes["excitement"] += 1
    if narrate:
        world.say(f"Then {actor.id} {activity.rush}.")
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"Once upon a time, there was a {desc} named {hero.id}.")


def loves_market(world: World, hero: Entity) -> None:
    hero.memes["love"] += 1
    where = "the open-air lanes" if not world.market.indoor else "the market hall"
    world.say(f"{hero.id} loved walking through {where} and hearing all the little calls.")


def buy_token(world: World, parent: Entity, hero: Entity, coin: Entity) -> None:
    world.say(
        f"One day, {parent.label_word.capitalize()} gave {hero.pronoun('object')} a new "
        f"{coin.label} for the market."
    )


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"One sunny morning, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} went to {world.market.label}."
    )


def want_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f'{hero.id} said, "I want to {activity.verb} today."')


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, coin: Entity) -> bool:
    pred = predict_loss(world, hero, activity)
    if not pred["lost"]:
        return False
    world.facts["predicted_loss"] = True
    world.facts["risk_reason"] = (
        f"{activity.gerund.capitalize()} would jostle {hero.id}'s pocket, "
        f"so the {coin.label} could slip out in the crowd."
    )
    world.say(
        f'"Careful," {parent.pronoun()} said. "If you start {activity.gerund}, '
        f'that {coin.label} will drop from {hero.pronoun("possessive")} pocket before we get home."'
    )
    return True


def resist(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(f'{hero.id} frowned and said, "But I have to try!"')


def grab_hand(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Then {parent.label_word.capitalize()} gently grabbed '
        f'{hero.pronoun("object")} by the hand.'
    )


def offer_gear(world: World, parent: Entity, hero: Entity, coin: Entity,
               activity: Activity) -> Optional[Pouch]:
    gear_def = select_gear(activity, COINS[coin.id])
    if gear_def is None:
        return None
    world.say(
        f'"Take my {gear_def.label}," {parent.pronoun()} said, '
        f'"then you can keep exploring safely."'
    )
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="pouch",
        label=gear_def.label,
        owner=parent.id,
        worn_by=hero.id,
        protective=True,
        covers=set(gear_def.covers),
    ))
    world.facts["gear"] = gear
    world.facts["resolved"] = True
    world.say(
        f'{parent.label_word.capitalize()} helped {hero.id} '
        f'put {coin.phrase or coin.label} inside the {gear.label}.'
    )
    return gear_def


def accept(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["relief"] += 1
    parent.memes["joy"] += 1
    world.say(
        f'{hero.id} nodded. "Okay, I can do that," {hero.pronoun()} said. '
        f'{parent.pronoun().capitalize()} smiled.'
    )


def play(world: World, hero: Entity, activity: Activity) -> None:
    _do_activity(world, hero, activity)


def finish_market_trip(world: World, hero: Entity, parent: Entity, coin_id: str) -> None:
    coin = world.entities[coin_id]
    if coin.meters["lost"] >= THRESHOLD:
        world.facts["outcome"] = "lost"
        hero.memes["sadness"] += 1
        world.say(
            f'{coin.id.capitalize()} was gone by the time they reached the fruit stall. '
            f'{hero.id} felt sad, and the day became a little quieter.'
        )
        return

    world.facts["outcome"] = "safe"
    world.say(
        f'{hero.id} and {hero.pronoun("possessive")} {parent.label_word} reached the candy stand.'
    )
    world.say(
        f'{hero.id} handed over {coin.phrase or coin.label} and bought a sweet for the two of them.'
    )
    world.say(f'At the end of the visit, {hero.id} hugged {hero.pronoun("possessive")} {parent.label_word} happily.')


def tell(params: StoryParams) -> World:
    world = World(MARKETS[params.market])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
    ))
    coin_cfg = COINS[params.coin]
    coin = world.add(Entity(
        id=coin_cfg.id,
        kind="thing",
        type="coin",
        label=coin_cfg.label,
        phrase=coin_cfg.phrase,
        owner=hero.id,
        region=coin_cfg.region,
        plural=coin_cfg.plural,
    ))

    activity = ACTIVITIES[params.activity]
    world.facts.update({
        "hero": hero.id,
        "parent": parent.id,
        "coin_id": coin.id,
        "activity": activity.id,
    })

    introduce(world, hero)
    loves_market(world, hero)
    world.para()
    buy_token(world, parent, hero, coin)
    arrive(world, hero, parent)
    want_activity(world, hero, activity)
    warned = warn(world, parent, hero, activity, coin)

    if warned:
        resist(world, hero)
        grab_hand(world, parent, hero)
        offer = offer_gear(world, parent, hero, coin, activity)
        if offer is None:
            world.facts["resolved"] = False
            world.say(
                f'The idea was sensible, but nothing nearby could hold the coin safely right now.'
            )
            resist(world, hero)
        else:
            accept(world, hero, parent)
            world.para()
            world.say(
                f'They chose the {offer.label} and walked through the crowd together at a slower pace.'
            )
    else:
        world.facts["resolved"] = False
        world.say(f'There was no hurry today, and {hero.id} agreed to stay close.')

    play(world, hero, activity)
    finish_market_trip(world, hero, parent, coin.id)
    return world


def generation_prompts(world: World) -> list[str]:
    act = ACTIVITIES[world.facts["activity"]]
    coin = COINS[world.facts["coin_id"]]
    place = world.market.label
    kw = act.keyword or act.id
    return [
        f'Write a short story for a child about a visit to a market, where a child says "I want to {act.verb}".',
        f"The story should include a coin, a crowded market, and how the child keeps from losing it.",
        f"Use the word \"{kw}\" and end with the child still having enough to buy a treat at the market in {place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.entities[world.facts["hero"]]
    parent = world.entities[world.facts["parent"]]
    act = ACTIVITIES[world.facts["activity"]]
    coin = world.entities[world.facts["coin_id"]]
    place = world.market.label
    outcome = world.facts.get("outcome")
    conflict = bool(world.facts.get("resolved"))

    qa: list[tuple[str, str]] = [
        ("Who is the story about?", f"It is about {hero.id} and {hero.pronoun('possessive')} {parent.label_word} visiting {place}."),
        (
            f"What did {hero.id} want to do at the market?",
            f"{hero.id} wanted to {act.verb}.",
        ),
        (
            "What is this story's central object?",
            f"The key object was a {coin.label}.",
        ),
        (
            f"Why did {parent.label_word.capitalize()} warn {hero.id}?",
            world.facts.get("risk_reason", f"{parent.label_word} did not think there was a risk."),
        ),
    ]
    if conflict:
        qa.append((
            "How did they avoid losing the coin?",
            f"They used the {world.facts['gear'].label if world.facts.get('gear') else 'coin pouch'} "
            f"so the coin stayed safe while playing."
        ))
    if outcome == "safe":
        qa.append((f"How did {hero.id} finish the visit?",
                   f"{hero.id} reached the candy stand, paid with the coin, and bought a sweet for the two of them to share."))
    else:
        qa.append((f"What happened by the end of the market visit?",
                   f"{hero.id} lost {hero.pronoun('possessive')} coin and could not buy anything."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    act = ACTIVITIES[world.facts["activity"]]
    coin = COINS[world.facts["coin_id"]]
    tags: set[str] = {act.id, act.risk, coin.id, "market", "coin"}
    if world.facts.get("resolved"):
        tags.add("pouch")
    out: list[tuple[str, str]] = []
    for key in [
        "coin", "market", "crowd", "pouch", "warning", "activity", "loss",
    ]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE.get(key, []))
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
    for ent in world.entities.values():
        bits: list[str] = []
        if ent.region:
            bits.append(f"region={ent.region}")
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by}")
        if ent.covers:
            bits.append(f"covers={sorted(ent.covers)}")
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: {sorted(world.facts.items())}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, market in MARKETS.items():
        for activity_id, activity in ACTIVITIES.items():
            if activity_id not in market.affords:
                continue
            for coin_id, coin in COINS.items():
                if not prize_at_risk(activity, coin):
                    continue
                if select_gear(activity, coin) is None:
                    continue
                combos.append((place, activity_id, coin_id))
    return sorted(set(combos))


def explain_rejection(activity: Activity, coin: Coin) -> str:
    if not prize_at_risk(activity, coin):
        return (
            f"(No story: the activity '{activity.id}' does not threaten a coin "
            f"in a {coin.region}, so this warning case is not compatible.)"
        )
    return (
        f"(No story: this activity can lose a pocket coin, but no listed gear makes it safe. "
        f"Try another activity or coin choice.)"
    )


MARKETS: dict[str, Market] = {
    "old_town": Market(
        "old_town",
        "the old-town market",
        indoor=False,
        affords={"chase_balloon", "thread_between_stalls", "count_crates"},
    ),
    "harbor": Market(
        "harbor",
        "the harbor market",
        indoor=False,
        affords={"chase_balloon", "thread_between_stalls", "fruit_tasting"},
    ),
    "night_market": Market(
        "night_market",
        "the lantern night market",
        indoor=False,
        affords={"chase_balloon", "thread_between_stalls", "fruit_tasting"},
    ),
}


ACTIVITIES: dict[str, Activity] = {
    "chase_balloon": Activity(
        "chase_balloon",
        "chase a silver balloon through the stalls",
        "chasing the silver balloon, weaving between shoppers",
        "chased the silver balloon while weaving between shoppers",
        zones={"pocket"},
        risk="loss",
        keyword="balloon",
        tags={"speed", "crowd", "coin"},
    ),
    "thread_between_stalls": Activity(
        "thread_between_stalls",
        "thread between the crowded stalls",
        "weaving through the stalls and staying close to the row",
        "weaved through the stalls and stayed near the side",
        zones={"pocket"},
        risk="loss",
        keyword="stalls",
        tags={"crowd", "careful", "coin"},
    ),
    "fruit_tasting": Activity(
        "fruit_tasting",
        "taste fresh fruit at the edge of a stall",
        "standing by the fruit table and choosing a pear",
        "stood by the fruit table and chose a pear",
        zones={"pocket", "hands"},
        risk="loss",
        keyword="fruit",
        tags={"stalls", "coin"},
    ),
    "count_crates": Activity(
        "count_crates",
        "help count crates that are stacked too high",
        "counting the crates with tiny steps",
        "helped count crates with tiny steps",
        zones={"hands"},
        risk="slip",
        keyword="crate",
        tags={"calm", "safe"},
    ),
}


COINS: dict[str, Coin] = {
    "copper": Coin(
        "copper",
        "copper coin",
        "a bright copper coin",
        region="pocket",
    ),
    "silver": Coin(
        "silver",
        "silver coin",
        "a shiny silver coin",
        region="pocket",
    ),
    "token": Coin(
        "token",
        "market token",
        "a lucky market token",
        region="pocket",
    ),
}


GEAR: list[Pouch] = [
    Pouch(
        "coin_purse",
        "coin purse",
        covers={"pocket"},
        guards={"loss"},
        offer="Use this clasped coin purse",
        tail="walk together at a slower pace",
    ),
    Pouch(
        "crossbody_bag",
        "crossbody bag",
        covers={"pocket"},
        guards={"loss"},
        offer="Slip the coin in the crossbody bag",
        tail="keep your hands free in the crowd",
    ),
]


BOY_NAMES = ["Leo", "Kai", "Sam", "Noah", "Owen", "Milo"]
GIRL_NAMES = ["Mia", "Lina", "Nora", "Aya", "Zoe", "Ivy"]
TRAITS = ["curious", "playful", "bold", "careful"]


WORLD_KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "coin": [
        ("Why can a coin be lost in a crowd?",
         "A pocket can be jostled and the object can fall out if it is not held or "
         "stored safely."),
        ("Why use a small purse for coins?",
         "A coin purse gives the coins a separate, closed space, so they are less "
         "likely to fall out during movement."),
    ],
    "pouch": [
        ("What is a coin purse?",
         "A coin purse is a tiny bag for small coins that keeps them from slipping "
         "out of a pocket."),
    ],
    "market": [
        ("Why does a market feel crowded?",
         "Many people walk through market aisles at once, so people and carts "
         "can squeeze close together."),
    ],
    "crowd": [
        ("What should you do in a crowded place if you need to keep something safe?",
         "Walk at a slower pace and keep your hands or valuables close."
         ),
    ],
    "warning": [
        ("Why might grown-ups warn in crowds?",
         "Adults often warn to prevent avoidable accidents like losing money or running "
         "into people."),
    ],
    "activity": [
        ("Why is chasing things in busy places risky?",
         "Fast movement in dense spaces can cause collisions and make it harder to "
         "keep small items from falling out."),
    ],
    "loss": [
        ("What should you do if you drop something important?",
         "Tell an adult right away and pause your activity while you both look for "
         "it."),
    ],
}


CURATED: list[StoryParams] = [
    StoryParams("old_town", "chase_balloon", "copper", "Mia", "girl", "mother", "careful"),
    StoryParams("harbor", "thread_between_stalls", "silver", "Leo", "boy", "father", "curious"),
    StoryParams("night_market", "fruit_tasting", "token", "Aya", "girl", "mother", "playful"),
    StoryParams("old_town", "chase_balloon", "silver", "Kai", "boy", "father", "bold"),
]


ASP_RULES = r"""
% A coin can be at risk only when the activity jostles the region where it is carried.
prize_at_risk(A, C) :- activity_zone(A, R), coin_region(C, R).

% A compatible tool must guard loss and protect the at-risk region.
has_fix(A, C, G) :- gear(G), prize_at_risk(A, C),
                     activity_risk(A, R), guards(G, R),
                     covers(G, R2), coin_region(C, R2).

% Reasonable stories require an affordable place, an at-risk coin, and at least one fix.
valid(M, A, C) :- place(M), affords(M, A), prize_at_risk(A, C), has_fix(A, C, _).
valid_story(M, A, C, G) :- valid(M, A, C), has_fix(A, C, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, market in MARKETS.items():
        lines.append(asp.fact("place", key))
        for activity_id in sorted(market.affords):
            lines.append(asp.fact("affords", key, activity_id))
    for key, activity in ACTIVITIES.items():
        lines.append(asp.fact("activity", key))
        lines.append(asp.fact("activity_risk", key, activity.risk))
        for zone in sorted(activity.zones):
            lines.append(asp.fact("activity_zone", key, zone))
    for key, coin in COINS.items():
        lines.append(asp.fact("coin", key))
        lines.append(asp.fact("coin_region", key, coin.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for risk in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, risk))
        for region in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print(f"  only in clingo: {sorted(clingo_set - python_set)}")
    if python_set - clingo_set:
        print(f"  only in python: {sorted(python_set - clingo_set)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a market visit, a loose coin, and a safe compromise."
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--market", choices=MARKETS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--coin", choices=COINS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.market and args.activity and args.coin:
        activity = ACTIVITIES[args.activity]
        coin = COINS[args.coin]
        if not (prize_at_risk(activity, coin) and select_gear(activity, coin)):
            raise StoryError(explain_rejection(activity, coin))

    combos = [c for c in valid_combos()
              if (args.market is None or c[0] == args.market)
              and (args.activity is None or c[1] == args.activity)
              and (args.coin is None or c[2] == args.coin)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, coin = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, coin, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3.\n#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (market, activity, coin) combos ({len(stories)} with gear):\n")
        for market, activity, coin in triples:
            options = [gear for (m, a, c, gear) in stories if (m, a, c) == (market, activity, coin)]
            print(f"  {market:10} {activity:22} {coin:8}  [{', '.join(sorted(options))}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
        for idx, s in enumerate(samples):
            if s.world is not None:
                s.params.seed = base_seed + idx
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.market} with {p.coin}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
