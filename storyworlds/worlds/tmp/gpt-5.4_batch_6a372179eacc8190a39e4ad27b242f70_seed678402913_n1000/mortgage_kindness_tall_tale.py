#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mortgage_kindness_tall_tale.py
=========================================================

A standalone storyworld for a tall-tale kindness story built around one concrete
problem: a neighbor's farm will be lost unless today's harvest can cover the
mortgage by sunset.

The world model keeps the logic narrow and child-facing:

* a worried neighbor has a real mortgage due
* a famously kind giant-hearted helper chooses one impossible-but-coherent feat
* that feat increases one kind of harvest
* the harvest must fit the chosen delivery method
* when the crop is sold, the money either covers the mortgage or the story is
  rejected before generation

This lets the prose come from state: worry, promise, giant action, market run,
payment, and a changed ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/mortgage_kindness_tall_tale.py
    python storyworlds/worlds/gpt-5.4/mortgage_kindness_tall_tale.py --crop apples --feat hill_roll --delivery barge
    python storyworlds/worlds/gpt-5.4/mortgage_kindness_tall_tale.py --mortgage thunder_big
    python storyworlds/worlds/gpt-5.4/mortgage_kindness_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/mortgage_kindness_tall_tale.py --qa
    python storyworlds/worlds/gpt-5.4/mortgage_kindness_tall_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    opening: str
    market: str
    landmark: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Crop:
    id: str
    label: str
    patch: str
    unit: str
    harvest_word: str
    kind: str
    base_yield: int
    price: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Feat:
    id: str
    label: str
    action: str
    bonus: int
    works_on: set[str] = field(default_factory=set)
    image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Delivery:
    id: str
    label: str
    phrase: str
    capacity: int = 0
    image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mortgage:
    id: str
    label: str
    amount: int
    due_line: str
    tags: set[str] = field(default_factory=set)


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


def _r_sellable_money(world: World) -> list[str]:
    out: list[str] = []
    crop = world.get("crop")
    neighbor = world.get("neighbor")
    if crop.meters["harvest"] < THRESHOLD:
        return out
    sig = ("money", int(crop.meters["harvest"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    earned = int(crop.meters["harvest"]) * int(crop.attrs["price"])
    neighbor.meters["earned"] = float(earned)
    out.append("__money__")
    return out


def _r_paid_relief(world: World) -> list[str]:
    out: list[str] = []
    neighbor = world.get("neighbor")
    mortgage = world.get("mortgage")
    helper = world.get("helper")
    lender = world.get("lender")
    if neighbor.meters["earned"] < mortgage.meters["due"]:
        return out
    sig = ("paid",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mortgage.meters["paid"] = mortgage.meters["due"]
    neighbor.memes["worry"] = 0.0
    neighbor.memes["relief"] += 2
    helper.memes["joy"] += 1
    lender.memes["softened"] += 1
    out.append("__paid__")
    return out


CAUSAL_RULES = [
    Rule(name="sellable_money", tag="physical", apply=_r_sellable_money),
    Rule(name="paid_relief", tag="social", apply=_r_paid_relief),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "prairie": Place(
        id="prairie",
        label="the Prairie of Long Shadows",
        opening="where fence posts looked like toothpicks and evening winds hummed through the grass",
        market="the Saturday market by the water tower",
        landmark="a windmill that creaked louder than a fiddle",
        tags={"farm"},
    ),
    "riverbend": Place(
        id="riverbend",
        label="Riverbend Hollow",
        opening="where the creek bent twice before breakfast and barns threw long blue shade",
        market="the dock market under the grain elevator",
        landmark="a silver creek with banks as soft as cake",
        tags={"river"},
    ),
    "redmesa": Place(
        id="redmesa",
        label="Red Mesa Flats",
        opening="where the sunset painted every fence rail copper",
        market="the trading square beside the red stone well",
        landmark="a stone well so deep it seemed to sip clouds",
        tags={"mesa"},
    ),
}

CROPS = {
    "apples": Crop(
        id="apples",
        label="apples",
        patch="orchard",
        unit="crate",
        harvest_word="crates of apples",
        kind="tree",
        base_yield=6,
        price=3,
        tags={"apple", "fruit"},
    ),
    "pumpkins": Crop(
        id="pumpkins",
        label="pumpkins",
        patch="pumpkin patch",
        unit="wagonload",
        harvest_word="wagonloads of pumpkins",
        kind="vine",
        base_yield=5,
        price=4,
        tags={"pumpkin", "vegetable"},
    ),
    "corn": Crop(
        id="corn",
        label="corn",
        patch="cornfield",
        unit="bundle",
        harvest_word="bundles of corn",
        kind="stalk",
        base_yield=7,
        price=2,
        tags={"corn", "grain"},
    ),
}

FEATS = {
    "hill_roll": Feat(
        id="hill_roll",
        label="rolled a hill smooth as dough",
        action="rolled the nearest hill across the field as gently as a baker rolls pie crust",
        bonus=4,
        works_on={"vine", "stalk"},
        image="The ground turned so rich and fluffy that roots seemed to laugh under it.",
        tags={"soil", "tall"},
    ),
    "moon_hum": Feat(
        id="moon_hum",
        label="hummed moonlight into bloom",
        action="stood at the field edge and hummed so low that even the moon leaned down to listen",
        bonus=5,
        works_on={"tree", "vine"},
        image="Every leaf shone, and the fruit swelled as if each one had secretly swallowed a lantern.",
        tags={"moon", "tall"},
    ),
    "wind_braid": Feat(
        id="wind_braid",
        label="braided the wind through the rows",
        action="caught three stripes of wind and braided them through the rows with both hands",
        bonus=6,
        works_on={"stalk"},
        image="The stalks stood up straighter than soldiers and filled out ear by ear.",
        tags={"wind", "tall"},
    ),
}

DELIVERIES = {
    "wagon": Delivery(
        id="wagon",
        label="wagon",
        phrase="an old hickory wagon",
        capacity=10,
        image="Its wheels sang over the ruts like banjos.",
        tags={"wagon"},
    ),
    "barge": Delivery(
        id="barge",
        label="barge",
        phrase="a flat river barge",
        capacity=12,
        image="It slid along the water as calm as a sleepy duck.",
        tags={"river"},
    ),
    "sled": Delivery(
        id="sled",
        label="sled",
        phrase="a broad barn sled",
        capacity=9,
        image="It skimmed over the dry ground as if the dust had turned to ice just to help.",
        tags={"sled"},
    ),
}

MORTGAGES = {
    "porch_small": Mortgage(
        id="porch_small",
        label="small mortgage",
        amount=18,
        due_line="The farm needed only a little more money before sunset, but little can still feel enormous when a paper says mortgage across the top.",
        tags={"mortgage"},
    ),
    "thunder_big": Mortgage(
        id="thunder_big",
        label="thundering mortgage",
        amount=28,
        due_line="A thundering mortgage payment was due by sunset, and the paper looked heavy enough to bend the kitchen table.",
        tags={"mortgage"},
    ),
    "windmill_medium": Mortgage(
        id="windmill_medium",
        label="windmill-sized mortgage",
        amount=24,
        due_line="A windmill-sized mortgage bill was due that very evening, and every tick of the clock sounded like a boot heel on the porch.",
        tags={"mortgage"},
    ),
}

HELPER_NAMES = ["Mae", "June", "Tess", "Ruth", "Nell", "Eli", "Bo", "Hank", "Cal", "Jude"]
HELPER_TYPES = {
    "Mae": "woman",
    "June": "woman",
    "Tess": "woman",
    "Ruth": "woman",
    "Nell": "woman",
    "Eli": "man",
    "Bo": "man",
    "Hank": "man",
    "Cal": "man",
    "Jude": "man",
}
NEIGHBOR_NAMES = ["Mira", "Sadie", "Clara", "Ben", "Owen", "Silas", "Nora", "Pete"]
NEIGHBOR_TYPES = {
    "Mira": "woman",
    "Sadie": "woman",
    "Clara": "woman",
    "Nora": "woman",
    "Ben": "man",
    "Owen": "man",
    "Silas": "man",
    "Pete": "man",
}
LENDER_NAMES = ["Mr. Pennygood", "Mrs. Ledger", "Old Miss Brass", "Mr. Quill"]

KNOWLEDGE = {
    "mortgage": [
        (
            "What is a mortgage?",
            "A mortgage is money a family borrows to buy a home or farm and then pays back over time. If they cannot pay it, they can be in danger of losing that place.",
        )
    ],
    "market": [
        (
            "What is a market?",
            "A market is a place where people bring things to sell and other people come to buy them. Farmers often take crops there to earn money.",
        )
    ],
    "wagon": [
        (
            "What is a wagon for?",
            "A wagon helps carry heavy things from one place to another. Farmers use wagons to move crops and tools.",
        )
    ],
    "river": [
        (
            "What is a barge?",
            "A barge is a flat boat made to carry heavy loads on water. It can move many things that would be hard to haul by hand.",
        )
    ],
    "pumpkin": [
        (
            "Where do pumpkins grow?",
            "Pumpkins grow on long vines close to the ground. They start as flowers and then grow bigger and bigger.",
        )
    ],
    "apple": [
        (
            "Where do apples grow?",
            "Apples grow on trees in an orchard. A tree can hold many apples on its branches.",
        )
    ],
    "corn": [
        (
            "How does corn grow?",
            "Corn grows on tall stalks in rows. Each stalk can make ears of corn as it grows.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, comfort, or care for someone. It often means using your strength for another person's good.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mortgage", "kindness", "market", "wagon", "river", "pumpkin", "apple", "corn"]


def total_yield(crop: Crop, feat: Feat) -> int:
    return crop.base_yield + feat.bonus


def money_earned(crop: Crop, feat: Feat) -> int:
    return total_yield(crop, feat) * crop.price


def feat_supports(feat: Feat, crop: Crop) -> bool:
    return crop.kind in feat.works_on


def delivery_fits(crop: Crop, feat: Feat, delivery: Delivery) -> bool:
    return delivery.capacity >= total_yield(crop, feat)


def covers_mortgage(crop: Crop, feat: Feat, mortgage: Mortgage) -> bool:
    return money_earned(crop, feat) >= mortgage.amount


def valid_combo(crop: Crop, feat: Feat, delivery: Delivery, mortgage: Mortgage) -> bool:
    return feat_supports(feat, crop) and delivery_fits(crop, feat, delivery) and covers_mortgage(crop, feat, mortgage)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for crop_id, crop in CROPS.items():
        for feat_id, feat in FEATS.items():
            for delivery_id, delivery in DELIVERIES.items():
                if feat_supports(feat, crop) and delivery_fits(crop, feat, delivery):
                    combos.append((crop_id, feat_id, delivery_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    crop: str
    feat: str
    delivery: str
    mortgage: str
    helper_name: str
    neighbor_name: str
    lender_name: str
    seed: Optional[int] = None


def predict_plan(world: World, crop_id: str, feat_id: str, delivery_id: str, mortgage_id: str) -> dict:
    crop_cfg = CROPS[crop_id]
    feat_cfg = FEATS[feat_id]
    delivery_cfg = DELIVERIES[delivery_id]
    mortgage_cfg = MORTGAGES[mortgage_id]
    return {
        "supported": feat_supports(feat_cfg, crop_cfg),
        "yield": total_yield(crop_cfg, feat_cfg),
        "money": money_earned(crop_cfg, feat_cfg),
        "fits": delivery_fits(crop_cfg, feat_cfg, delivery_cfg),
        "pays": covers_mortgage(crop_cfg, feat_cfg, mortgage_cfg),
    }


def introduce(world: World, place: Place, helper: Entity) -> None:
    world.say(
        f"In {place.label}, {place.opening}, lived {helper.id}, a giant-hearted {helper.type} whose kindness was said to be wider than a hayfield."
    )
    world.say(
        f"People claimed {helper.pronoun()} could lift a fence with one hand and soothe a crying calf with the other, and both stories sounded true."
    )


def show_problem(world: World, place: Place, neighbor: Entity, crop: Crop, mortgage: Mortgage) -> None:
    neighbor.memes["worry"] += 2
    world.say(
        f"Down by {place.landmark}, {neighbor.id} stood beside {neighbor.pronoun('possessive')} {crop.patch} with a folded paper in {neighbor.pronoun('possessive')} hand."
    )
    world.say(mortgage.due_line)
    world.say(
        f"{neighbor.pronoun().capitalize()} had a good {crop.patch}, but not enough ready to sell, and worry made {neighbor.pronoun('possessive')} shoulders droop."
    )


def kindness_promise(world: World, helper: Entity, neighbor: Entity, lender: Entity, plan: dict, crop: Crop) -> None:
    helper.memes["kindness"] += 2
    neighbor.memes["hope"] += 1
    world.facts["predicted_money"] = plan["money"]
    world.facts["predicted_yield"] = plan["yield"]
    world.say(
        f'{helper.id} read the paper, saw the word "mortgage," and set {helper.pronoun("possessive")} hat over {helper.pronoun("possessive")} heart.'
    )
    world.say(
        f'"No neighbor of mine is losing a home while I still have breath in my chest," {helper.pronoun()} said. "{crop.harvest_word.capitalize()} are going to march to market before {lender.id} can clear {lender.pronoun("possessive")} throat."'
    )


def perform_feat(world: World, helper: Entity, feat: Feat, crop: Crop) -> None:
    crop_ent = world.get("crop")
    crop_ent.meters["harvest"] = float(total_yield(crop, feat))
    crop_ent.meters["base_harvest"] = float(crop.base_yield)
    crop_ent.meters["bonus_harvest"] = float(feat.bonus)
    helper.memes["effort"] += 1
    world.say(
        f"So {helper.id} {feat.action}. {feat.image}"
    )
    world.say(
        f"By the time {helper.pronoun()} stepped back, the {crop.patch} held {total_yield(crop, feat)} {crop.unit if total_yield(crop, feat) == 1 else crop.unit + 's'} worth of {crop.label}."
    )
    propagate(world, narrate=False)


def load_delivery(world: World, helper: Entity, neighbor: Entity, delivery: Delivery, crop: Crop) -> None:
    crop_ent = world.get("crop")
    crop_ent.meters["loaded"] = crop_ent.meters["harvest"]
    world.say(
        f"Then {helper.id} and {neighbor.id} loaded the harvest onto {delivery.phrase}. {delivery.image}"
    )


def market_sale(world: World, place: Place, neighbor: Entity, crop: Crop) -> None:
    earned = int(neighbor.meters["earned"])
    world.say(
        f"They reached {place.market}, and people came running from every stall to stare at those towering {crop.label}."
    )
    world.say(
        f"Before the church bell could finish one slow ring, every last bit was sold, and {neighbor.id} counted out {earned} silver dollars into a flour sack."
    )


def pay_lender(world: World, neighbor: Entity, lender: Entity, mortgage: Mortgage) -> None:
    neighbor.meters["cash_on_hand"] = neighbor.meters["earned"]
    propagate(world, narrate=False)
    world.say(
        f"{neighbor.id} walked straight to {lender.id}, poured the money onto the desk, and paid the {mortgage.label} in full."
    )
    world.say(
        f"{lender.id} blinked twice, softened all around the eyes, and slid the paper back with a small respectful nod."
    )


def ending(world: World, place: Place, helper: Entity, neighbor: Entity, crop: Crop) -> None:
    helper.memes["joy"] += 1
    helper.memes["kindness"] += 1
    neighbor.memes["gratitude"] += 2
    world.say(
        f"That evening smoke rose from {neighbor.id}'s chimney instead of worry, and supper tasted better for being safe at home."
    )
    world.say(
        f"Folks in {place.label} said the tallest thing {helper.id} ever did was not making the {crop.patch} grow so grand. It was using all that impossible strength for kindness."
    )


def tell(
    place: Place,
    crop: Crop,
    feat: Feat,
    delivery: Delivery,
    mortgage: Mortgage,
    helper_name: str,
    neighbor_name: str,
    lender_name: str,
) -> World:
    world = World()
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=HELPER_TYPES[helper_name],
            label=helper_name,
            role="helper",
            traits=["strong", "kind"],
        )
    )
    neighbor = world.add(
        Entity(
            id=neighbor_name,
            kind="character",
            type=NEIGHBOR_TYPES[neighbor_name],
            label=neighbor_name,
            role="neighbor",
            traits=["hardworking"],
        )
    )
    lender_type = "woman" if lender_name.startswith("Mrs.") or lender_name.startswith("Miss") else "man"
    lender = world.add(
        Entity(
            id=lender_name,
            kind="character",
            type=lender_type,
            label=lender_name,
            role="lender",
            traits=["stern"],
        )
    )
    crop_ent = world.add(
        Entity(
            id="crop",
            type="crop",
            label=crop.label,
            phrase=crop.harvest_word,
            attrs={"price": crop.price, "unit": crop.unit, "patch": crop.patch},
            tags=set(crop.tags),
        )
    )
    mortgage_ent = world.add(
        Entity(
            id="mortgage",
            type="paper",
            label="mortgage paper",
            phrase="the mortgage paper",
            tags={"mortgage"},
        )
    )
    mortgage_ent.meters["due"] = float(mortgage.amount)

    plan = predict_plan(world, crop.id, feat.id, delivery.id, mortgage.id)
    if not plan["supported"]:
        raise StoryError(explain_rejection(crop, feat, delivery, mortgage))
    if not plan["fits"]:
        raise StoryError(explain_rejection(crop, feat, delivery, mortgage))
    if not plan["pays"]:
        raise StoryError(explain_rejection(crop, feat, delivery, mortgage))

    introduce(world, place, helper)
    show_problem(world, place, neighbor, crop, mortgage)

    world.para()
    kindness_promise(world, helper, neighbor, lender, plan, crop)
    perform_feat(world, helper, feat, crop)
    load_delivery(world, helper, neighbor, delivery, crop)

    world.para()
    market_sale(world, place, neighbor, crop)
    pay_lender(world, neighbor, lender, mortgage)

    world.para()
    ending(world, place, helper, neighbor, crop)

    world.facts.update(
        place=place,
        crop_cfg=crop,
        feat_cfg=feat,
        delivery_cfg=delivery,
        mortgage_cfg=mortgage,
        helper=helper,
        neighbor=neighbor,
        lender=lender,
        crop=crop_ent,
        mortgage=mortgage_ent,
        predicted_yield=plan["yield"],
        predicted_money=plan["money"],
        paid=mortgage_ent.meters["paid"] >= mortgage_ent.meters["due"],
        earned=int(neighbor.meters["earned"]),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    helper = f["helper"]
    neighbor = f["neighbor"]
    crop = f["crop_cfg"]
    return [
        'Write a short Tall Tale for a 3-to-5-year-old that includes the word "mortgage" and centers on Kindness.',
        f"Tell a gentle tall tale where {helper.id} uses impossible farm strength to help {neighbor.id} save a home by selling {crop.label}.",
        f'Write a story with a huge, playful exaggeration, but make the biggest thing in it be kindness rather than bragging.',
    ]


def pair_role(entity: Entity) -> str:
    return "woman" if entity.type == "woman" else "man"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper = f["helper"]
    neighbor = f["neighbor"]
    lender = f["lender"]
    crop = f["crop_cfg"]
    feat = f["feat_cfg"]
    delivery = f["delivery_cfg"]
    mortgage = f["mortgage_cfg"]
    earned = f["earned"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {helper.id}, a giant-hearted {pair_role(helper)}, and {neighbor.id}, the neighbor {helper.pronoun()} chose to help. {lender.id} matters too because that was the person waiting for the mortgage payment.",
        ),
        (
            f"Why was {neighbor.id} worried?",
            f"{neighbor.id} was worried because a {mortgage.label} was due by sunset. If the money was not paid, {neighbor.pronoun()} could lose the farm and home.",
        ),
        (
            f"What kind thing did {helper.id} do?",
            f"{helper.id} promised not to let a neighbor lose a home and then used that huge tall-tale strength to help the {crop.patch}. The kindness came first, and the giant feat followed because of it.",
        ),
        (
            f"How did {helper.id} make the harvest bigger?",
            f"{helper.pronoun().capitalize()} {feat.action}. Because of that, the {crop.patch} grew to {f['predicted_yield']} {crop.unit if f['predicted_yield'] == 1 else crop.unit + 's'} worth of {crop.label}.",
        ),
        (
            "How did they get the harvest to town?",
            f"They loaded it onto {delivery.phrase} and took it to {f['place'].market}. The trip mattered because a huge harvest only helps if it can reach buyers.",
        ),
        (
            "How was the mortgage solved?",
            f"They sold the harvest for {earned} silver dollars and paid the mortgage in full. That money changed the ending from fear and worry to relief and supper at home.",
        ),
        (
            "What proves the story ends happily?",
            f"The chimney smoke rose from {neighbor.id}'s house instead of worry, so the family could stay home. The final image shows safety, food, and thankfulness after the payment was made.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mortgage", "kindness", "market"}
    crop = f["crop_cfg"]
    delivery = f["delivery_cfg"]
    tags |= set(crop.tags)
    tags |= set(delivery.tags)
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
    for e in world.entities.values():
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:14} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="prairie",
        crop="pumpkins",
        feat="hill_roll",
        delivery="wagon",
        mortgage="porch_small",
        helper_name="Mae",
        neighbor_name="Ben",
        lender_name="Mr. Pennygood",
    ),
    StoryParams(
        place="riverbend",
        crop="apples",
        feat="moon_hum",
        delivery="barge",
        mortgage="windmill_medium",
        helper_name="Eli",
        neighbor_name="Nora",
        lender_name="Mrs. Ledger",
    ),
    StoryParams(
        place="redmesa",
        crop="corn",
        feat="wind_braid",
        delivery="barge",
        mortgage="thunder_big",
        helper_name="Tess",
        neighbor_name="Silas",
        lender_name="Old Miss Brass",
    ),
    StoryParams(
        place="prairie",
        crop="corn",
        feat="hill_roll",
        delivery="barge",
        mortgage="porch_small",
        helper_name="Bo",
        neighbor_name="Clara",
        lender_name="Mr. Quill",
    ),
]


def explain_rejection(crop: Crop, feat: Feat, delivery: Delivery, mortgage: Mortgage) -> str:
    if not feat_supports(feat, crop):
        return (
            f"(No story: the feat '{feat.id}' does not sensibly help {crop.label}. "
            f"This world only allows tall-tale magic that still matches the kind of crop.)"
        )
    if not delivery_fits(crop, feat, delivery):
        return (
            f"(No story: {delivery.phrase} cannot carry {total_yield(crop, feat)} loads of {crop.label}. "
            f"The harvest has to fit the delivery method to reach market.)"
        )
    if not covers_mortgage(crop, feat, mortgage):
        return (
            f"(No story: selling the {crop.label} would not cover the {mortgage.label}. "
            f"A story here needs a real kindness fix, not a pretend solution.)"
        )
    return "(No story: that combination does not make a reasonable plan.)"


ASP_RULES = r"""
supports(F, C) :- works_on(F, K), crop_kind(C, K).
yield(C, F, Y) :- base_yield(C, B), bonus(F, X), Y = B + X.
fits(C, F, D) :- yield(C, F, Y), capacity(D, Cap), Cap >= Y.
pays(C, F, M) :- yield(C, F, Y), price(C, P), due(M, A), Y * P >= A.
valid(C, F, D, M) :- crop(C), feat(F), delivery(D), mortgage(M), supports(F, C), fits(C, F, D), pays(C, F, M).

outcome(paid) :- chosen_crop(C), chosen_feat(F), chosen_delivery(D), chosen_mortgage(M), valid(C, F, D, M).
outcome(rejected) :- chosen_crop(C), chosen_feat(F), chosen_delivery(D), chosen_mortgage(M), not valid(C, F, D, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, crop in CROPS.items():
        lines.append(asp.fact("crop", cid))
        lines.append(asp.fact("crop_kind", cid, crop.kind))
        lines.append(asp.fact("base_yield", cid, crop.base_yield))
        lines.append(asp.fact("price", cid, crop.price))
    for fid, feat in FEATS.items():
        lines.append(asp.fact("feat", fid))
        lines.append(asp.fact("bonus", fid, feat.bonus))
        for kind in sorted(feat.works_on):
            lines.append(asp.fact("works_on", fid, kind))
    for did, delivery in DELIVERIES.items():
        lines.append(asp.fact("delivery", did))
        lines.append(asp.fact("capacity", did, delivery.capacity))
    for mid, mortgage in MORTGAGES.items():
        lines.append(asp.fact("mortgage", mid))
        lines.append(asp.fact("due", mid, mortgage.amount))
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
            asp.fact("chosen_crop", params.crop),
            asp.fact("chosen_feat", params.feat),
            asp.fact("chosen_delivery", params.delivery),
            asp.fact("chosen_mortgage", params.mortgage),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    crop = CROPS[params.crop]
    feat = FEATS[params.feat]
    delivery = DELIVERIES[params.delivery]
    mortgage = MORTGAGES[params.mortgage]
    return "paid" if valid_combo(crop, feat, delivery, mortgage) else "rejected"


def asp_verify() -> int:
    rc = 0
    python_set = {
        (crop_id, feat_id, delivery_id, mortgage_id)
        for crop_id, crop in CROPS.items()
        for feat_id, feat in FEATS.items()
        for delivery_id, delivery in DELIVERIES.items()
        for mortgage_id, mortgage in MORTGAGES.items()
        if valid_combo(crop, feat, delivery, mortgage)
    }
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid combos ({len(python_set)} combinations).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    rng = random.Random(123)
    parser = build_parser()
    for _ in range(12):
        try:
            params = resolve_params(parser.parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale kindness storyworld: a giant-hearted neighbor helps save a farm from a mortgage."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--feat", choices=FEATS)
    ap.add_argument("--delivery", choices=DELIVERIES)
    ap.add_argument("--mortgage", choices=MORTGAGES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--neighbor-name", choices=NEIGHBOR_NAMES)
    ap.add_argument("--lender-name", choices=LENDER_NAMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crop and args.feat and not feat_supports(FEATS[args.feat], CROPS[args.crop]):
        raise StoryError(explain_rejection(CROPS[args.crop], FEATS[args.feat], DELIVERIES[args.delivery or "wagon"], MORTGAGES[args.mortgage or "porch_small"]))

    combos = [
        (crop_id, feat_id, delivery_id, mortgage_id)
        for crop_id, crop in CROPS.items()
        for feat_id, feat in FEATS.items()
        for delivery_id, delivery in DELIVERIES.items()
        for mortgage_id, mortgage in MORTGAGES.items()
        if (args.crop is None or crop_id == args.crop)
        and (args.feat is None or feat_id == args.feat)
        and (args.delivery is None or delivery_id == args.delivery)
        and (args.mortgage is None or mortgage_id == args.mortgage)
        and valid_combo(crop, feat, delivery, mortgage)
    ]
    if not combos:
        crop = CROPS[args.crop] if args.crop else next(iter(CROPS.values()))
        feat = FEATS[args.feat] if args.feat else next(iter(FEATS.values()))
        delivery = DELIVERIES[args.delivery] if args.delivery else next(iter(DELIVERIES.values()))
        mortgage = MORTGAGES[args.mortgage] if args.mortgage else next(iter(MORTGAGES.values()))
        raise StoryError(explain_rejection(crop, feat, delivery, mortgage))

    crop_id, feat_id, delivery_id, mortgage_id = rng.choice(sorted(combos))
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    neighbor_name = args.neighbor_name or rng.choice([n for n in NEIGHBOR_NAMES if n != helper_name])
    lender_name = args.lender_name or rng.choice(LENDER_NAMES)
    place = args.place or rng.choice(sorted(PLACES))
    return StoryParams(
        place=place,
        crop=crop_id,
        feat=feat_id,
        delivery=delivery_id,
        mortgage=mortgage_id,
        helper_name=helper_name,
        neighbor_name=neighbor_name,
        lender_name=lender_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop: {params.crop})")
    if params.feat not in FEATS:
        raise StoryError(f"(Unknown feat: {params.feat})")
    if params.delivery not in DELIVERIES:
        raise StoryError(f"(Unknown delivery: {params.delivery})")
    if params.mortgage not in MORTGAGES:
        raise StoryError(f"(Unknown mortgage: {params.mortgage})")
    if params.helper_name not in HELPER_NAMES:
        raise StoryError(f"(Unknown helper name: {params.helper_name})")
    if params.neighbor_name not in NEIGHBOR_NAMES:
        raise StoryError(f"(Unknown neighbor name: {params.neighbor_name})")
    if params.lender_name not in LENDER_NAMES:
        raise StoryError(f"(Unknown lender name: {params.lender_name})")

    world = tell(
        place=PLACES[params.place],
        crop=CROPS[params.crop],
        feat=FEATS[params.feat],
        delivery=DELIVERIES[params.delivery],
        mortgage=MORTGAGES[params.mortgage],
        helper_name=params.helper_name,
        neighbor_name=params.neighbor_name,
        lender_name=params.lender_name,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (crop, feat, delivery, mortgage) combos:\n")
        for crop, feat, delivery, mortgage in combos:
            print(f"  {crop:10} {feat:10} {delivery:8} {mortgage}")
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
            header = f"### {p.helper_name} helps {p.neighbor_name}: {p.crop}, {p.feat}, {p.delivery}, {p.mortgage}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
