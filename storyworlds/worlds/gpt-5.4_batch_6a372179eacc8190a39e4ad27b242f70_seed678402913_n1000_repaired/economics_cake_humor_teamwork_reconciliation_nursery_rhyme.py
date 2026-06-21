#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/economics_cake_humor_teamwork_reconciliation_nursery_rhyme.py
================================================================================================

A small standalone storyworld about two children running a tiny cake stall in a
nursery-rhyme mood. The world is built around a simple bit of economics:
the cake must be divided in a sensible way, and the chosen price must be fair
enough for the crowd and strong enough to earn back the baking cost.

The emotional shape is equally important:
- Humor: a dab of icing and a silly laugh loosen the quarrel.
- Teamwork: one child cuts while the other counts.
- Reconciliation: hurt feelings are repaired with an apology and shared work.

Run it
------
    python storyworlds/worlds/gpt-5.4/economics_cake_humor_teamwork_reconciliation_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/economics_cake_humor_teamwork_reconciliation_nursery_rhyme.py --cake berry --crowd ducks --service slices --price one
    python storyworlds/worlds/gpt-5.4/economics_cake_humor_teamwork_reconciliation_nursery_rhyme.py --service whole
    python storyworlds/worlds/gpt-5.4/economics_cake_humor_teamwork_reconciliation_nursery_rhyme.py --all --qa
    python storyworlds/worlds/gpt-5.4/economics_cake_humor_teamwork_reconciliation_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import math
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class CakeKind:
    id: str
    label: str
    phrase: str
    flavor: str
    crumb: str
    base_slices: int
    bake_cost: int
    max_price: int
    rhyme_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CrowdKind:
    id: str
    label: str
    phrase: str
    demand: int
    arrival: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ServicePlan:
    id: str
    label: str
    phrase: str
    servings_kind: str
    rhyme_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PricePlan:
    id: str
    label: str
    coins: int
    boast: str
    fairness_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    cake: str
    crowd: str
    service: str
    price: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    seed: Optional[int] = None


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def servings_for(cake: CakeKind, service: ServicePlan) -> int:
    if service.servings_kind == "whole":
        return 1
    if service.servings_kind == "halves":
        return 2
    if service.servings_kind == "slices":
        return cake.base_slices
    raise StoryError(f"(Unknown service plan: {service.id})")


def revenue_for(cake: CakeKind, crowd: CrowdKind, service: ServicePlan, price: PricePlan) -> int:
    return min(servings_for(cake, service), crowd.demand) * price.coins


def fair_offer(cake: CakeKind, crowd: CrowdKind, service: ServicePlan, price: PricePlan) -> bool:
    return (
        servings_for(cake, service) >= crowd.demand
        and price.coins <= cake.max_price
        and revenue_for(cake, crowd, service, price) >= cake.bake_cost
    )


def outcome_of_params(params: StoryParams) -> str:
    cake = CAKES[params.cake]
    crowd = CROWDS[params.crowd]
    service = SERVICES[params.service]
    if servings_for(cake, service) == crowd.demand:
        return "sold_out"
    return "leftover"


def explain_rejection(cake: CakeKind, crowd: CrowdKind, service: ServicePlan, price: PricePlan) -> str:
    servings = servings_for(cake, service)
    revenue = revenue_for(cake, crowd, service, price)
    if servings < crowd.demand:
        return (
            f"(No story: serving the {cake.label} as {service.label} makes only {servings} serving"
            f"{'' if servings == 1 else 's'}, but {crowd.label} need {crowd.demand}. "
            f"A teamwork market story needs enough cake to share fairly.)"
        )
    if price.coins > cake.max_price:
        return (
            f"(No story: {price.coins} coin{'s' if price.coins != 1 else ''} per serving is too steep "
            f"for a {cake.label}. The economics of this little world prefer a fairer price.)"
        )
    if revenue < cake.bake_cost:
        return (
            f"(No story: selling to {crowd.label} at {price.coins} coin{'s' if price.coins != 1 else ''} each "
            f"would earn only {revenue} coin{'s' if revenue != 1 else ''}, not enough to cover the "
            f"{cake.bake_cost}-coin baking cost. The stall would not work.)"
        )
    return "(No story: that cake offer does not make sense in this world.)"


def predicted_offer(world: World, cake: CakeKind, crowd: CrowdKind, service: ServicePlan, price: PricePlan) -> dict:
    sim = world.copy()
    stand = sim.get("stand")
    stand.attrs["open"] = True
    stand.attrs["demand"] = crowd.demand
    stand.attrs["servings"] = servings_for(cake, service)
    stand.attrs["price"] = price.coins
    stand.attrs["bake_cost"] = cake.bake_cost
    stand.attrs["fair"] = fair_offer(cake, crowd, service, price)
    propagate(sim, narrate=False)
    return {
        "sold": int(sim.get("crowd").meters["served"]),
        "coins": int(sim.get("stand").meters["coins"]),
        "left": int(sim.get("cake").meters["servings_left"]),
        "fair": bool(sim.get("stand").attrs["fair"]),
    }


def _r_sales(world: World) -> list[str]:
    stand = world.entities.get("stand")
    cake = world.entities.get("cake")
    crowd = world.entities.get("crowd")
    if not stand or not cake or not crowd:
        return []
    if not stand.attrs.get("open") or not stand.attrs.get("fair"):
        return []
    sig = ("sales", stand.attrs.get("servings"), stand.attrs.get("price"), stand.attrs.get("demand"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sold = min(int(stand.attrs.get("servings", 0)), int(stand.attrs.get("demand", 0)))
    stand.meters["coins"] += sold * int(stand.attrs.get("price", 0))
    stand.meters["customers"] += sold
    cake.meters["servings_left"] = max(0.0, float(stand.attrs.get("servings", 0) - sold))
    crowd.meters["served"] += sold
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    return ["__sales__"]


def _r_reconcile(world: World) -> list[str]:
    kids = world.kids()
    if len(kids) != 2:
        return []
    a, b = kids
    if a.memes["apology"] < THRESHOLD or b.memes["apology"] < THRESHOLD:
        return []
    sig = ("reconcile", a.id, b.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["forgiven"] += 1
    b.memes["forgiven"] += 1
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    return ["__reconcile__"]


def _r_teamwork(world: World) -> list[str]:
    kids = world.kids()
    stand = world.entities.get("stand")
    if len(kids) != 2 or not stand or not stand.attrs.get("open"):
        return []
    if not all(k.attrs.get("job") for k in kids):
        return []
    sig = ("teamwork", kids[0].id, kids[1].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in kids:
        kid.memes["teamwork"] += 1
    return ["__teamwork__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="sales", tag="economics", apply=_r_sales),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


CAKES = {
    "berry": CakeKind(
        id="berry",
        label="berry cake",
        phrase="a round berry cake",
        flavor="berry",
        crumb="purple crumbs",
        base_slices=4,
        bake_cost=3,
        max_price=2,
        rhyme_line="Round went the spoon for the berry cake bright.",
        tags={"cake", "berries"},
    ),
    "honey": CakeKind(
        id="honey",
        label="honey cake",
        phrase="a golden honey cake",
        flavor="honey",
        crumb="golden crumbs",
        base_slices=6,
        bake_cost=4,
        max_price=2,
        rhyme_line="Golden the honey cake glowed in the light.",
        tags={"cake", "honey"},
    ),
    "plum": CakeKind(
        id="plum",
        label="plum cake",
        phrase="a tall plum cake",
        flavor="plum",
        crumb="violet crumbs",
        base_slices=8,
        bake_cost=6,
        max_price=3,
        rhyme_line="Tall stood the plum cake, proud as a kite.",
        tags={"cake", "plums"},
    ),
}

CROWDS = {
    "ducks": CrowdKind(
        id="ducks",
        label="four ducks",
        phrase="four waddling ducks",
        demand=4,
        arrival="Down the lane came four ducks, quacking in a row.",
        ending="The ducks went home with sticky bills and happy feet.",
        tags={"ducks", "sharing"},
    ),
    "lambs": CrowdKind(
        id="lambs",
        label="six lambs",
        phrase="six skipping lambs",
        demand=6,
        arrival="Over the grass came six lambs, bobbing white and slow.",
        ending="The lambs skipped off licking crumbs from their woolly lips.",
        tags={"lambs", "sharing"},
    ),
    "mice": CrowdKind(
        id="mice",
        label="eight mice",
        phrase="eight market mice",
        demand=8,
        arrival="Round the barrel scampered eight mice, whiskers all a-twitch.",
        ending="The mice hurried home with neat paws and bright eyes.",
        tags={"mice", "sharing"},
    ),
}

SERVICES = {
    "whole": ServicePlan(
        id="whole",
        label="one whole cake",
        phrase="sell it as one whole cake",
        servings_kind="whole",
        rhyme_line="Whole was too grand for a crowd at the gate.",
        tags={"whole", "sharing"},
    ),
    "halves": ServicePlan(
        id="halves",
        label="two big halves",
        phrase="cut it into two big halves",
        servings_kind="halves",
        rhyme_line="Half and a half still left many to wait.",
        tags={"halves", "sharing"},
    ),
    "slices": ServicePlan(
        id="slices",
        label="small slices",
        phrase="cut it into small slices",
        servings_kind="slices",
        rhyme_line="Slice after slice made the sharing feel straight.",
        tags={"slices", "sharing"},
    ),
}

PRICES = {
    "one": PricePlan(
        id="one",
        label="one coin",
        coins=1,
        boast="One coin! A tidy and twinkly call!",
        fairness_line="One coin was gentle and easy to pay.",
        tags={"economics", "coins"},
    ),
    "two": PricePlan(
        id="two",
        label="two coins",
        coins=2,
        boast="Two coins! A grand little market decree!",
        fairness_line="Two coins still worked when the cake had enough worth.",
        tags={"economics", "coins"},
    ),
    "three": PricePlan(
        id="three",
        label="three coins",
        coins=3,
        boast="Three coins! cried the boldest tongue first.",
        fairness_line="Three coins fit only the tallest cake best.",
        tags={"economics", "coins"},
    ),
}

GIRL_NAMES = ["Dot", "May", "Nell", "Tess", "Molly", "June", "Poppy", "Ruth"]
BOY_NAMES = ["Pip", "Ned", "Tom", "Jem", "Will", "Finn", "Kit", "Ben"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for cake_id, cake in CAKES.items():
        for crowd_id, crowd in CROWDS.items():
            for service_id, service in SERVICES.items():
                for price_id, price in PRICES.items():
                    if fair_offer(cake, crowd, service, price):
                        out.append((cake_id, crowd_id, service_id, price_id))
    return out


CURATED = [
    StoryParams(
        cake="berry",
        crowd="ducks",
        service="slices",
        price="one",
        child1="Pip",
        child1_gender="boy",
        child2="Dot",
        child2_gender="girl",
    ),
    StoryParams(
        cake="honey",
        crowd="lambs",
        service="slices",
        price="one",
        child1="May",
        child1_gender="girl",
        child2="Ned",
        child2_gender="boy",
    ),
    StoryParams(
        cake="honey",
        crowd="ducks",
        service="slices",
        price="two",
        child1="Jem",
        child1_gender="boy",
        child2="Tess",
        child2_gender="girl",
    ),
    StoryParams(
        cake="plum",
        crowd="mice",
        service="slices",
        price="one",
        child1="Poppy",
        child1_gender="girl",
        child2="Finn",
        child2_gender="boy",
    ),
    StoryParams(
        cake="plum",
        crowd="lambs",
        service="slices",
        price="three",
        child1="Ruth",
        child1_gender="girl",
        child2="Kit",
        child2_gender="boy",
    ),
]


def open_rhyme(world: World, a: Entity, b: Entity, cake: CakeKind) -> None:
    for kid in (a, b):
        kid.memes["hope"] += 1
    world.say(
        f"{a.id} and {b.id} set up a tiny table by the garden gate, neat as a song."
    )
    world.say(
        f"They had baked {cake.phrase}, and it smelled of {cake.flavor} and warm afternoon air."
    )
    world.say(cake.rhyme_line)
    world.say(
        f'"Let us make a market!" sang {a.id}. "Let us make a snack and a plan!"'
    )


def economics_problem(
    world: World,
    a: Entity,
    b: Entity,
    cake: CakeKind,
    crowd: CrowdKind,
    service: ServicePlan,
    price: PricePlan,
) -> None:
    stand = world.get("stand")
    pred = predicted_offer(world, cake, crowd, service, price)
    stand.attrs["prediction"] = pred
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    world.say(crowd.arrival)
    world.say(
        f'{a.id} puffed up and cried, "{price.boast} We shall {service.phrase}!"'
    )
    world.say(
        f"{b.id} counted on small fingers and peeped at the pan. "
        f'"But we have {servings_for(cake, service)} servings for {crowd.demand} hungry noses," '
        f"{b.pronoun()} said."
    )
    world.say(
        f'Then {b.id} whispered, "This is economics: count the cost, count the cake, and count the friends."'
    )
    world.say(
        f"{b.id} tapped the recipe card. "
        f'"The flour and fruit cost {cake.bake_cost} coins to bake. '
        f"If we are fair and we share, we can earn {pred['coins']} coins and still be kind.\""
    )


def icing_joke(world: World, a: Entity, b: Entity) -> None:
    a.memes["embarrassed"] += 1
    b.memes["embarrassed"] += 1
    world.say(
        f"As they argued, a spot of icing landed on {a.id}'s lip and curled like a white moustache."
    )
    world.say(
        f'{b.id} gave one surprised snort, then another, then a giggle that bounced like a spoon in a cup.'
    )
    world.say(
        f"{a.id} almost frowned, but when {b.id} pointed to the funny moustache, "
        f"{a.pronoun()} saw it in the shiny pan and laughed too."
    )


def apologize(world: World, a: Entity, b: Entity) -> None:
    a.memes["apology"] += 1
    b.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I was being bossy," said {a.id}. "I wanted the biggest call at the gate."'
    )
    world.say(
        f'"I laughed before I was gentle," said {b.id}. "I am sorry for that."'
    )
    world.say(
        f"They touched sticky fingers, and the quarrel softened like sugar in warm milk."
    )


def plan_jobs(world: World, a: Entity, b: Entity, service: ServicePlan) -> None:
    a.attrs["job"] = "cutter"
    b.attrs["job"] = "counter"
    world.get("stand").attrs["open"] = True
    propagate(world, narrate=False)
    world.say(
        f'"You cut," said {b.id}, "and I will count."'
    )
    world.say(
        f'"Done," said {a.id}, taking a careful knife. Together they chose to {service.phrase}.'
    )


def sell(world: World, cake: CakeKind, crowd: CrowdKind, service: ServicePlan, price: PricePlan) -> None:
    stand = world.get("stand")
    stand.attrs["servings"] = servings_for(cake, service)
    stand.attrs["demand"] = crowd.demand
    stand.attrs["price"] = price.coins
    stand.attrs["bake_cost"] = cake.bake_cost
    stand.attrs["fair"] = fair_offer(cake, crowd, service, price)
    world.get("cake").meters["servings_left"] = float(servings_for(cake, service))
    propagate(world, narrate=False)
    sold = int(world.get("crowd").meters["served"])
    left = int(world.get("cake").meters["servings_left"])
    world.say(
        f"So slice by slice, and coin by coin, they served {sold} little customers."
    )
    world.say(
        f"{price.fairness_line} The coins clinked in the tin like polite, bright rain."
    )
    if left == 0:
        world.say(
            "Not a crumb was left but a sweet smell and a shining plate."
        )
    else:
        world.say(
            f"There were {left} pieces left on the tray, enough for a shared teatime after the stall."
        )


def ending(world: World, a: Entity, b: Entity, cake: CakeKind, crowd: CrowdKind) -> None:
    stand = world.get("stand")
    coins = int(stand.meters["coins"])
    cost = cake.bake_cost
    left = int(world.get("cake").meters["servings_left"])
    if left == 0:
        world.say(
            f'{crowd.ending} {a.id} and {b.id} counted {coins} coins and smiled at the empty plate.'
        )
        world.say(
            f'"Back enough for flour, and back enough for fun," said {a.id}.'
        )
    else:
        world.say(
            f'{crowd.ending} {a.id} and {b.id} counted {coins} coins, then split the last bites between themselves.'
        )
        world.say(
            f'"Back enough for flour, and one little treat besides," said {b.id}.'
        )
    if coins >= cost:
        world.say(
            "That was the happy economics of the day: fair cake, fair pay, and no one left out."
        )
    world.say(
        f"And by the gate in the late gold light, two small bakers worked side by side, "
        f"their laughter softer than before and stronger too."
    )


def tell(
    cake: CakeKind,
    crowd: CrowdKind,
    service: ServicePlan,
    price: PricePlan,
    child1: str,
    child1_gender: str,
    child2: str,
    child2_gender: str,
) -> World:
    world = World()
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="seller"))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="seller"))
    world.add(Entity(id="cake", type="cake", label=cake.label, phrase=cake.phrase))
    world.add(Entity(id="crowd", type="crowd", label=crowd.label))
    world.add(Entity(id="stand", type="stand", label="cake stand", attrs={"open": False}))
    world.facts.update(
        cake_cfg=cake,
        crowd_cfg=crowd,
        service_cfg=service,
        price_cfg=price,
        child1=a,
        child2=b,
    )

    open_rhyme(world, a, b, cake)
    world.para()
    economics_problem(world, a, b, cake, crowd, service, price)
    icing_joke(world, a, b)
    apologize(world, a, b)
    world.para()
    plan_jobs(world, a, b, service)
    sell(world, cake, crowd, service, price)
    ending(world, a, b, cake, crowd)

    world.facts.update(
        servings=servings_for(cake, service),
        revenue=int(world.get("stand").meters["coins"]),
        bake_cost=cake.bake_cost,
        outcome="sold_out" if world.get("cake").meters["servings_left"] < THRESHOLD else "leftover",
        reconciled=a.memes["forgiven"] >= THRESHOLD and b.memes["forgiven"] >= THRESHOLD,
        teamwork=a.memes["teamwork"] >= THRESHOLD and b.memes["teamwork"] >= THRESHOLD,
        sold=int(world.get("crowd").meters["served"]),
        left=int(world.get("cake").meters["servings_left"]),
    )
    return world


KNOWLEDGE = {
    "economics": [
        (
            "What does economics mean in a small market?",
            "Economics means thinking about what something costs, what people need, and what price is fair. "
            "In a little cake stall, it helps you decide how to share the cake and earn enough coins to bake again."
        )
    ],
    "coins": [
        (
            "Why do shops use coins?",
            "Coins are one way to pay for things. They help people trade fairly instead of guessing what something is worth."
        )
    ],
    "cake": [
        (
            "Why do people cut a cake into slices?",
            "They cut a cake into slices so more people can share it. Smaller pieces make sharing easier and fairer."
        )
    ],
    "sharing": [
        (
            "Why is sharing important in a team?",
            "Sharing helps everyone take part and keeps one person from taking too much. "
            "It also makes it easier to solve problems together."
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology tells someone you know you hurt their feelings and want to make things better. "
            "It can help a friendship feel safe again."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people do different helpful jobs together. "
            "One person might cut while another counts, and the job goes better because they cooperate."
        )
    ],
}

KNOWLEDGE_ORDER = ["economics", "coins", "cake", "sharing", "apology", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cake = f["cake_cfg"]
    crowd = f["crowd_cfg"]
    price = f["price_cfg"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "economics" and "cake".',
        f"Tell a gentle humorous story where two children sell {cake.label} to {crowd.label}, quarrel a little, then reconcile and work as a team.",
        f"Write a small market story where children choose a fair price of {price.label} for cake, learn simple economics, and end side by side in friendship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    cake = f["cake_cfg"]
    crowd = f["crowd_cfg"]
    service = f["service_cfg"]
    price = f["price_cfg"]
    sold = f["sold"]
    left = f["left"]
    revenue = f["revenue"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children who opened a tiny cake stall together. "
            f"They had baked {cake.phrase} and wanted to sell it kindly."
        ),
        (
            "What was the problem at the cake stall?",
            f"They started to quarrel over how to sell the cake and what price to call out. "
            f"The problem was not just the cake itself, but how to share it fairly and make the stall work."
        ),
        (
            "How did the story use economics?",
            f"{b.id} counted the servings, the baking cost, and the coins they could earn. "
            f"That simple counting helped them choose a fair plan instead of just the loudest idea."
        ),
        (
            "What funny thing happened while they argued?",
            f"A dab of icing landed on {a.id}'s lip like a little white moustache. "
            f"The silly sight made them laugh and helped the tight, cross feeling loosen."
        ),
        (
            "How did they make up after the quarrel?",
            f"They both said sorry: {a.id} admitted being bossy, and {b.id} admitted laughing without being gentle. "
            f"Because they apologized and listened, the quarrel softened and they could work together again."
        ),
        (
            "How did they work as a team?",
            f"{a.id} took the careful cutting job, and {b.id} counted the coins. "
            f"Each child had a part, so the stall ran smoothly and the sharing stayed fair."
        ),
    ]
    if left == 0:
        qa.append(
            (
                "Did they sell all the cake?",
                f"Yes. They served {sold} customers, and not a crumb was left on the plate. "
                f"That showed they had made just enough pieces for the crowd."
            )
        )
    else:
        qa.append(
            (
                "Was any cake left at the end?",
                f"Yes. They served {sold} customers and still had {left} pieces left on the tray. "
                f"The leftover cake became a treat they could share after the work was done."
            )
        )
    qa.append(
        (
            "Why was the price fair?",
            f"The price was {price.label} for each serving, which fit this kind of cake and brought in {revenue} coins. "
            f"That was enough to cover the {cake.bake_cost}-coin baking cost without asking too much from the crowd."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"economics", "coins", "cake", "sharing", "apology", "teamwork"}
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(C, Cr, S, P) :- servings(C, S, N), demand(Cr, D), N >= D,
                      price(P, Pc), max_price(C, M), Pc =< M,
                      revenue(C, Cr, S, P, R), bake_cost(C, B), R >= B.

outcome(sold_out) :- chosen(C, Cr, S, _), servings(C, S, N), demand(Cr, D), N = D.
outcome(leftover) :- chosen(C, Cr, S, _), servings(C, S, N), demand(Cr, D), N > D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cake_id, cake in CAKES.items():
        lines.append(asp.fact("cake", cake_id))
        lines.append(asp.fact("bake_cost", cake_id, cake.bake_cost))
        lines.append(asp.fact("max_price", cake_id, cake.max_price))
    for crowd_id, crowd in CROWDS.items():
        lines.append(asp.fact("crowd", crowd_id))
        lines.append(asp.fact("demand", crowd_id, crowd.demand))
    for service_id, service in SERVICES.items():
        lines.append(asp.fact("service", service_id))
    for price_id, price in PRICES.items():
        lines.append(asp.fact("price_plan", price_id))
        lines.append(asp.fact("price", price_id, price.coins))
    for cake_id, cake in CAKES.items():
        for service_id, service in SERVICES.items():
            serv = servings_for(cake, service)
            lines.append(asp.fact("servings", cake_id, service_id, serv))
            for crowd_id, crowd in CROWDS.items():
                for price_id, price in PRICES.items():
                    rev = revenue_for(cake, crowd, service, price)
                    lines.append(asp.fact("revenue", cake_id, crowd_id, service_id, price_id, rev))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen", params.cake, params.crowd, params.service, params.price),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Nursery-rhyme cake-stall storyworld with simple economics, humor, teamwork, and reconciliation."
    )
    ap.add_argument("--cake", choices=CAKES)
    ap.add_argument("--crowd", choices=CROWDS)
    ap.add_argument("--service", choices=SERVICES)
    ap.add_argument("--price", choices=PRICES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cake and args.crowd and args.service and args.price:
        cake = CAKES[args.cake]
        crowd = CROWDS[args.crowd]
        service = SERVICES[args.service]
        price = PRICES[args.price]
        if not fair_offer(cake, crowd, service, price):
            raise StoryError(explain_rejection(cake, crowd, service, price))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cake is None or combo[0] == args.cake)
        and (args.crowd is None or combo[1] == args.crowd)
        and (args.service is None or combo[2] == args.service)
        and (args.price is None or combo[3] == args.price)
    ]
    if not combos:
        cake = CAKES[args.cake] if args.cake else next(iter(CAKES.values()))
        crowd = CROWDS[args.crowd] if args.crowd else next(iter(CROWDS.values()))
        service = SERVICES[args.service] if args.service else next(iter(SERVICES.values()))
        price = PRICES[args.price] if args.price else next(iter(PRICES.values()))
        raise StoryError(explain_rejection(cake, crowd, service, price))

    cake_id, crowd_id, service_id, price_id = rng.choice(sorted(combos))
    child1, child1_gender = _pick_child(rng)
    child2, child2_gender = _pick_child(rng, avoid=child1)
    return StoryParams(
        cake=cake_id,
        crowd=crowd_id,
        service=service_id,
        price=price_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        cake = CAKES[params.cake]
        crowd = CROWDS[params.crowd]
        service = SERVICES[params.service]
        price = PRICES[params.price]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter choice: {err})") from err
    if not fair_offer(cake, crowd, service, price):
        raise StoryError(explain_rejection(cake, crowd, service, price))

    world = tell(
        cake=cake,
        crowd=crowd,
        service=service,
        price=price,
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
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
    parser = build_parser()
    for s in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = []
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of_params(params)
        if ao != po:
            mismatches.append((params, ao, po))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcome differences.")
        for params, ao, po in mismatches[:5]:
            print(" ", params, ao, po)

    try:
        sample = generate(CURATED[0])
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated and emitted a normal story.")
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
        print(f"{len(combos)} compatible (cake, crowd, service, price) combos:\n")
        for cake, crowd, service, price in combos:
            out = asp_outcome(
                StoryParams(
                    cake=cake,
                    crowd=crowd,
                    service=service,
                    price=price,
                    child1="Pip",
                    child1_gender="boy",
                    child2="Dot",
                    child2_gender="girl",
                )
            )
            print(f"  {cake:6} {crowd:6} {service:6} {price:5} -> {out}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.child1} & {p.child2}: {p.cake}, {p.crowd}, {p.service}, {p.price} ({outcome_of_params(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
