#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dot_drink_rhyme_tall_tale.py
======================================================

A standalone story world for a tiny Tall-Tale garden domain built from the seed
words "dot" and "drink" with an explicit rhyme feature.

Premise
-------
A child finds a strange seed with a bright little dot on it. The child gives the
seed a nourishing drink and chants a rhyme. In true tall-tale style, the sprout
shoots up far too fast and becomes ridiculous: a bean climbs past the shed, a
sunflower peeks over the clouds, or a pumpkin swells wide as a wheelbarrow.
When the growth grows too wild, a nearby grown-up uses the right kind of support
to steady it. The ending image proves what changed: the child still gets a
marvel, but now with care instead of bragging alone.

This world is intentionally constraint-checked:
- only plant-friendly drinks are allowed;
- the support/fix must match the crop;
- the outcome model is mirrored by an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/dot_drink_rhyme_tall_tale.py
    python storyworlds/worlds/gpt-5.4/dot_drink_rhyme_tall_tale.py --crop bean --drink soda
    python storyworlds/worlds/gpt-5.4/dot_drink_rhyme_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/dot_drink_rhyme_tall_tale.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "grandma"}
        male = {"boy", "father", "uncle", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandma": "grandma",
            "grandpa": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Crop:
    id: str
    label: str
    seed_mark: str
    sprout: str
    produce: str
    support_kind: str
    sturdy: int
    giant_image: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Drink:
    id: str
    label: str
    phrase: str
    strength: int
    nourishing: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    amount: int
    pour_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    support_kind: str
    sense: int
    text: str
    qa_text: str
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


def _r_growth(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["drink_strength"] < THRESHOLD:
        return []
    if ("growth",) in world.fired:
        return []
    world.fired.add(("growth",))
    growth = plant.meters["drink_strength"] + plant.meters["pour_amount"]
    plant.meters["height"] += growth
    plant.meters["giant"] += 1
    return ["__growth__"]


def _r_wobble(world: World) -> list[str]:
    plant = world.get("plant")
    crop = world.facts["crop_cfg"]
    if plant.meters["height"] <= crop.sturdy:
        return []
    if ("wobble",) in world.fired:
        return []
    world.fired.add(("wobble",))
    plant.meters["wobble"] += plant.meters["height"] - crop.sturdy
    world.get("child").memes["alarm"] += 1
    return ["__wobble__"]


def _r_support(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["supported"] < THRESHOLD:
        return []
    if ("support",) in world.fired:
        return []
    world.fired.add(("support",))
    plant.meters["wobble"] = 0.0
    world.get("child").memes["relief"] += 1
    return ["__support__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="growth", tag="physical", apply=_r_growth),
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="support", tag="social", apply=_r_support),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


CROPS = {
    "bean": Crop(
        id="bean",
        label="bean",
        seed_mark="a blue dot",
        sprout="bean sprout",
        produce="pods",
        support_kind="trellis",
        sturdy=4,
        giant_image="the vine whipped past the fence, tied itself in a curly knot around the clothesline, and waved leaves bigger than kites",
        ending_image="By supper, green pods hung in a long ladder from the trellis, and even the sparrows looked up to count them",
        tags={"bean", "garden"},
    ),
    "sunflower": Crop(
        id="sunflower",
        label="sunflower",
        seed_mark="a gold dot",
        sprout="sunflower shoot",
        produce="seeds",
        support_kind="stake",
        sturdy=5,
        giant_image="the stalk rose so fast it seemed to poke the afternoon and borrow a little extra sunshine",
        ending_image="At dusk, the sunflower stood tall beside its stake, with a face broad as a wagon wheel and seeds packed in neat rows",
        tags={"sunflower", "garden"},
    ),
    "pumpkin": Crop(
        id="pumpkin",
        label="pumpkin",
        seed_mark="an orange dot",
        sprout="pumpkin sprout",
        produce="pumpkins",
        support_kind="straw_ring",
        sturdy=4,
        giant_image="the vine rolled across the patch, and one pumpkin puffed out until it looked fit to carry geese across a pond",
        ending_image="By evening, the pumpkin rested in its straw ring, round and glowing, while the child patted it like a sleepy orange moon",
        tags={"pumpkin", "garden"},
    ),
}

DRINKS = {
    "rainwater": Drink(
        id="rainwater",
        label="rainwater",
        phrase="a cool drink of rainwater",
        strength=2,
        nourishing=True,
        tags={"water", "garden"},
    ),
    "compost_tea": Drink(
        id="compost_tea",
        label="compost tea",
        phrase="a dark drink of compost tea",
        strength=3,
        nourishing=True,
        tags={"garden", "compost"},
    ),
    "dew_tea": Drink(
        id="dew_tea",
        label="dew tea",
        phrase="a sparkling drink of dew tea",
        strength=2,
        nourishing=True,
        tags={"garden", "water"},
    ),
    "soda": Drink(
        id="soda",
        label="soda",
        phrase="a fizzy drink of soda",
        strength=1,
        nourishing=False,
        tags={"soda"},
    ),
}

VESSELS = {
    "thimble": Vessel(
        id="thimble",
        label="thimble",
        phrase="a thimble",
        amount=1,
        pour_text="tipped in only a brave little sip",
        tags={"small", "measure"},
    ),
    "cup": Vessel(
        id="cup",
        label="cup",
        phrase="a polka-dot cup",
        amount=2,
        pour_text="poured a careful cupful with a very steady hand",
        tags={"cup", "dot", "measure"},
    ),
    "bucket": Vessel(
        id="bucket",
        label="bucket",
        phrase="a bucket",
        amount=3,
        pour_text="sloshed in a whole bucket with a grin too big for the garden gate",
        tags={"big", "measure"},
    ),
}

FIXES = {
    "trellis": Fix(
        id="trellis",
        label="trellis",
        support_kind="trellis",
        sense=3,
        text="set a stout trellis beside the plant and guided the racing vine onto it before it could lasso the laundry",
        qa_text="set up a trellis and guided the vine onto it",
        tags={"trellis", "support"},
    ),
    "stake": Fix(
        id="stake",
        label="stake",
        support_kind="stake",
        sense=3,
        text="pushed a strong stake into the earth and tied the tall stalk to it with a soft strip of cloth",
        qa_text="pushed in a stake and tied the stalk gently to it",
        tags={"stake", "support"},
    ),
    "straw_ring": Fix(
        id="straw_ring",
        label="straw ring",
        support_kind="straw_ring",
        sense=3,
        text="tucked a thick ring of straw under the swelling pumpkin so the giant fruit could rest without splitting the vine",
        qa_text="made a straw ring under the giant pumpkin",
        tags={"straw", "support"},
    ),
    "ribbon": Fix(
        id="ribbon",
        label="ribbon",
        support_kind="pretty_only",
        sense=1,
        text="tied a pretty ribbon on the plant and hoped prettiness would do the heavy work",
        qa_text="tied on a ribbon",
        tags={"ribbon"},
    ),
}

GIRL_NAMES = ["Mabel", "Daisy", "Nell", "Tilly", "Poppy", "Ruth", "Lula", "Maisie"]
BOY_NAMES = ["Jeb", "Otis", "Hank", "Beau", "Milo", "Clem", "Toby", "Eli"]
HELPERS = ["grandma", "grandpa", "aunt", "uncle"]
TRAITS = ["boastful", "bright-eyed", "eager", "stubborn", "cheerful", "plucky"]


def good_drink(drink: Drink) -> bool:
    return drink.nourishing


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fix_fits(crop: Crop, fix: Fix) -> bool:
    return fix.support_kind == crop.support_kind and fix.sense >= SENSE_MIN


def growth_score(crop: Crop, drink: Drink, vessel: Vessel) -> int:
    return drink.strength + vessel.amount


def needs_support(crop: Crop, drink: Drink, vessel: Vessel) -> bool:
    return growth_score(crop, drink, vessel) > crop.sturdy


def outcome_of(params: "StoryParams") -> str:
    crop = CROPS[params.crop]
    drink = DRINKS[params.drink]
    vessel = VESSELS[params.vessel]
    fix = FIXES[params.fix]
    if not good_drink(drink):
        raise StoryError(explain_drink(drink))
    if not fix_fits(crop, fix):
        raise StoryError(explain_fix(crop, fix))
    if needs_support(crop, drink, vessel):
        return "saved" if params.delay <= 1 else "flopped"
    return "steady"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for crop_id, crop in CROPS.items():
        for drink_id, drink in DRINKS.items():
            if not good_drink(drink):
                continue
            for vessel_id, _vessel in VESSELS.items():
                if any(fix_fits(crop, f) for f in sensible_fixes()):
                    combos.append((crop_id, drink_id, vessel_id))
    return combos


def explain_drink(drink: Drink) -> str:
    return (
        f"(No story: {drink.label} is not a sensible plant drink here. "
        "This world only allows nourishing drinks like rainwater, dew tea, or compost tea.)"
    )


def explain_fix(crop: Crop, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        good = ", ".join(sorted(f.id for f in sensible_fixes()))
        return (
            f"(Refusing fix '{fix.id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {good}.)"
        )
    return (
        f"(No story: a {crop.label} needs {crop.support_kind.replace('_', ' ')}, "
        f"not {fix.label}. The rescue must match the kind of plant that grew wild.)"
    )


def predict(world: World, crop: Crop, drink: Drink, vessel: Vessel) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    plant.meters["drink_strength"] += drink.strength
    plant.meters["pour_amount"] += vessel.amount
    propagate(sim, narrate=False)
    return {
        "height": plant.meters["height"],
        "wobble": plant.meters["wobble"],
        "needs_support": plant.meters["wobble"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, helper: Entity, crop: Crop) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"One windy morning, {child.id} found a {crop.label} seed in the garden, "
        f"and right in the middle of it sat {crop.seed_mark} like a tiny wink."
    )
    world.say(
        f'"A dot like that ought to grow a lot," said {child.id}, who was the sort of child '
        f"to say big things before breakfast."
    )
    world.say(
        f"{helper.label_word.capitalize()} chuckled and fetched a little spade while "
        f"{child.id} tucked the seed into the warm earth."
    )


def choose_drink(world: World, child: Entity, crop: Crop, drink: Drink, vessel: Vessel) -> None:
    child.memes["pride"] += 1
    world.say(
        f"Then {child.id} brought {vessel.phrase} filled with {drink.phrase}. "
        f"{child.pronoun().capitalize()} bent close to the patch and sang, "
        f'"Little dot, little spot, drink your drink and grow a lot!"'
    )
    world.say(f"{child.id} {vessel.pour_text}.")


def warn(world: World, helper: Entity, child: Entity, crop: Crop, drink: Drink, vessel: Vessel) -> None:
    pred = predict(world, crop, drink, vessel)
    world.facts["predicted_height"] = pred["height"]
    world.facts["predicted_wobble"] = pred["wobble"]
    if pred["needs_support"]:
        world.say(
            f'{helper.label_word.capitalize()} lifted an eyebrow. "That is a mighty drink for a '
            f"small {crop.sprout}," {helper.pronoun()} said. "
            '"Tall is fine, but tall and wobbly is trouble."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} nodded. "That ought to be enough drink to wake it up," '
            f'{helper.pronoun()} said.'
        )


def sprout_and_surge(world: World, child: Entity, crop: Crop, drink: Drink, vessel: Vessel) -> None:
    plant = world.get("plant")
    plant.meters["drink_strength"] += drink.strength
    plant.meters["pour_amount"] += vessel.amount
    child.memes["glee"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At once the ground gave a funny wiggle. Up popped a {crop.sprout}, and then up it went some more "
        f"until {crop.giant_image}."
    )
    if plant.meters["wobble"] >= THRESHOLD:
        world.say(
            f"For one breath, {child.id} grinned as wide as the gate. For the next, "
            f"{child.pronoun()} saw the giant growth lean and shiver."
        )


def fix_growth(world: World, helper: Entity, crop: Crop, fix: Fix) -> None:
    plant = world.get("plant")
    plant.meters["supported"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} did not fuss or flap. {helper.pronoun().capitalize()} {fix.text}."
    )


def too_late(world: World, child: Entity, helper: Entity, crop: Crop) -> None:
    plant = world.get("plant")
    plant.meters["flopped"] += 1
    child.memes["gloom"] += 1
    world.say(
        f"But the great green wonder tipped first. It flopped across the patch with a soft whomp, "
        f"like a sleepy giant lying down before supper."
    )
    world.say(
        f'{helper.label_word.capitalize()} put an arm around {child.id}. "A plant can love a drink," '
        f'{helper.pronoun()} said, "but even a tall tale grows better with a little measure."'
    )


def ending_steady(world: World, child: Entity, helper: Entity, crop: Crop) -> None:
    child.memes["pride"] += 1
    world.say(
        f"Soon the whole patch looked taller, brighter, and just wild enough to brag about. "
        f"{crop.ending_image}."
    )
    world.say(
        f'{child.id} clapped and sang one more rhyme: "Dot by dot, not by not, a careful drink can grow a lot!" '
        f"Even {helper.label_word} laughed at that."
    )


def ending_saved(world: World, child: Entity, helper: Entity, crop: Crop) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    world.say(
        f"The plant settled down, still enormous, but no longer wild. {crop.ending_image}."
    )
    world.say(
        f'{child.id} patted the dirt from {child.pronoun("possessive")} hands. "Next time," '
        f'{child.pronoun()} said, "I will keep the rhyme and mind the measure."'
    )


def ending_flopped(world: World, child: Entity, crop: Crop) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"Still, the patch was not empty. The bent green heap looked so grand and silly that "
        f"{child.id} could not help smiling through the disappointment."
    )
    world.say(
        f'From then on, whenever {child.id} brought a plant a drink, {child.pronoun()} used the little rhyme '
        f'and a steadier hand: "Little dot, little spot, just enough and not a lot."'
    )


def tell(
    crop: Crop,
    drink: Drink,
    vessel: Vessel,
    fix: Fix,
    child_name: str = "Mabel",
    child_gender: str = "girl",
    helper_type: str = "grandma",
    trait: str = "boastful",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, label=child_name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    plant = world.add(Entity(id="plant", kind="thing", type=crop.label, label=crop.label))
    child.attrs["trait"] = trait
    child.memes["confidence"] = 5.0

    opening(world, child, helper, crop)
    world.para()
    choose_drink(world, child, crop, drink, vessel)
    warn(world, helper, child, crop, drink, vessel)
    world.para()
    sprout_and_surge(world, child, crop, drink, vessel)

    outcome = "steady"
    if plant.meters["wobble"] >= THRESHOLD:
        world.para()
        if delay <= 1:
            fix_growth(world, helper, crop, fix)
            outcome = "saved"
            world.para()
            ending_saved(world, child, helper, crop)
        else:
            too_late(world, child, helper, crop)
            outcome = "flopped"
            world.para()
            ending_flopped(world, child, crop)
    else:
        world.para()
        ending_steady(world, child, helper, crop)

    world.facts.update(
        child=child,
        helper=helper,
        plant=plant,
        crop_cfg=crop,
        drink_cfg=drink,
        vessel_cfg=vessel,
        fix_cfg=fix,
        delay=delay,
        outcome=outcome,
        rhyme='Little dot, little spot, drink your drink and grow a lot!',
    )
    return world


@dataclass
class StoryParams:
    crop: str
    drink: str
    vessel: str
    fix: str
    child_name: str
    child_gender: str
    helper: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "garden": [
        (
            "What does a seed need to start growing?",
            "A seed usually needs water, warmth, and soil. After it wakes up, it also needs light and time."
        )
    ],
    "water": [
        (
            "Why do plants need a drink of water?",
            "Water helps a plant move food through its stem and leaves. Without enough water, a plant droops and cannot grow well."
        )
    ],
    "compost": [
        (
            "What is compost tea for plants?",
            "Compost tea is water that has picked up plant food from compost. Gardeners use it to help plants grow."
        )
    ],
    "trellis": [
        (
            "What is a trellis?",
            "A trellis is a frame that climbing plants can hold onto. It keeps long vines from tangling on the ground."
        )
    ],
    "stake": [
        (
            "Why would a gardener use a stake?",
            "A stake is a strong stick put beside a plant to help it stand up straight. Tall plants sometimes need that extra support."
        )
    ],
    "straw": [
        (
            "Why put straw under a pumpkin?",
            "Straw helps keep a heavy pumpkin dry and cushioned. That can protect the fruit and the vine."
        )
    ],
    "soda": [
        (
            "Why is soda not a good drink for a plant?",
            "Soda is sweet and fizzy, but plants are not looking for a treat. Plain water or plant food makes much more sense."
        )
    ],
}
KNOWLEDGE_ORDER = ["garden", "water", "compost", "trellis", "stake", "straw", "soda"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    crop = f["crop_cfg"]
    drink = f["drink_cfg"]
    vessel = f["vessel_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a tall-tale story for a 3-to-5-year-old that includes the words "dot" and "drink", '
        f'uses a simple rhyme, and features a child giving a {crop.label} seed {drink.label} from {vessel.phrase}.'
    )
    if outcome == "steady":
        return [
            base,
            f"Tell a playful tall tale where {child.id} sings a rhyme to a seed with {crop.seed_mark} and the plant grows huge but stays steady.",
            'Write a gentle garden tall tale with a rhyme like "Little dot, little spot" and a happy ending that shows careful measuring mattered.',
        ]
    if outcome == "saved":
        return [
            base,
            f"Tell a tall tale where {child.id}'s giant {crop.label} grows too fast after one mighty drink, but a grown-up uses the right support to save it.",
            "Write a rhyming story where bragging turns into careful help, and the ending image shows a marvelous giant plant standing safely.",
        ]
    return [
        base,
        f"Tell a cautionary tall tale where {child.id} gives a seed too much drink, the giant {crop.label} flops over, and the child learns to measure better next time.",
        'Write a story with a silly-big garden mistake, a rhyme, and a gentle lesson about "just enough and not a lot."',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    crop = f["crop_cfg"]
    drink = f["drink_cfg"]
    vessel = f["vessel_cfg"]
    fix = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in the garden, and {helper.label_word} who watches the growing plant. Together they deal with a tiny seed that turns into a very big tale."
        ),
        (
            "What was special about the seed?",
            f"The seed had {crop.seed_mark} on it. That little mark is why {child.id} began the rhyme about a dot before giving it a drink."
        ),
        (
            f"What did {child.id} give the seed to drink?",
            f"{child.id} gave the seed {drink.phrase} from {vessel.phrase}. The story makes that drink the spark that sends the plant shooting up."
        ),
        (
            "What rhyme did the child say?",
            f'{child.id} sang, "{f["rhyme"]}" The rhyme ties the seed\'s dot to the drink and the wild growing.'
        ),
    ]
    if outcome == "steady":
        qa.append(
            (
                f"Why did the plant stay steady?",
                f"It grew huge, but not too huge for a {crop.label} to hold. The drink and the amount were strong enough for wonder without making the plant wobble."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the giant plant still standing proudly in the garden. The final image showed that careful measuring can still lead to a marvelous tall-tale surprise."
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                f"Why did the giant {crop.label} need help?",
                f"It grew faster than its own stem or vine could manage, so it started to wobble. The mighty drink made the plant tall, but it also made support necessary."
            )
        )
        qa.append(
            (
                f"How did {helper.label_word} fix the problem?",
                f"{helper.label_word.capitalize()} {fix.qa_text}. That worked because a {crop.label} needs that kind of support when it grows too fast."
            )
        )
        qa.append(
            (
                f"What did {child.id} learn?",
                f"{child.id} learned that a rhyme can be fun, but a growing thing still needs care and measure. The story ends happily because the grown-up matched the rescue to the plant."
            )
        )
    else:
        qa.append(
            (
                f"Why did the giant {crop.label} flop over?",
                f"It grew too fast and too wild after the oversized drink, so it leaned before help could steady it. The trouble came from more growth than the plant could safely carry."
            )
        )
        qa.append(
            (
                "Was the ending all sad?",
                f"No. The child was disappointed, but still smiled at how grand and silly the plant looked. The ending turns the mistake into a lesson about using just enough."
            )
        )
        qa.append(
            (
                f"What did {child.id} do differently after that?",
                f"{child.id} kept the rhyme but used a steadier hand with future drinks. The change in the ending shows the child learned measure, not fear."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"garden"} | set(f["drink_cfg"].tags) | set(f["fix_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        crop="bean",
        drink="rainwater",
        vessel="cup",
        fix="trellis",
        child_name="Mabel",
        child_gender="girl",
        helper="grandma",
        trait="boastful",
        delay=0,
    ),
    StoryParams(
        crop="sunflower",
        drink="compost_tea",
        vessel="bucket",
        fix="stake",
        child_name="Jeb",
        child_gender="boy",
        helper="grandpa",
        trait="plucky",
        delay=1,
    ),
    StoryParams(
        crop="pumpkin",
        drink="dew_tea",
        vessel="thimble",
        fix="straw_ring",
        child_name="Daisy",
        child_gender="girl",
        helper="aunt",
        trait="cheerful",
        delay=0,
    ),
    StoryParams(
        crop="bean",
        drink="compost_tea",
        vessel="bucket",
        fix="trellis",
        child_name="Otis",
        child_gender="boy",
        helper="uncle",
        trait="eager",
        delay=2,
    ),
]


ASP_RULES = r"""
good_drink(D) :- drink(D), nourishing(D).
sensible_fix(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(C, D, V) :- crop(C), good_drink(D), vessel(V), crop_fix(C, Need), fix_kind(F, Need), sensible_fix(F).

growth(C, D, V, G) :- crop(C), drink(D), vessel(V), sturdy(C, _), strength(D, SD), amount(V, AV), G = SD + AV.
needs_support(C, D, V) :- growth(C, D, V, G), sturdy(C, S), G > S.

fit_fix(C, F) :- crop_fix(C, Need), fix_kind(F, Need), sensible_fix(F).

saved :- chosen_crop(C), chosen_drink(D), chosen_vessel(V), chosen_fix(F),
         fit_fix(C, F), needs_support(C, D, V), delay(T), T <= 1.
steady :- chosen_crop(C), chosen_drink(D), chosen_vessel(V), chosen_fix(F),
          fit_fix(C, F), not needs_support(C, D, V).
flopped :- chosen_crop(C), chosen_drink(D), chosen_vessel(V), chosen_fix(F),
           fit_fix(C, F), needs_support(C, D, V), delay(T), T > 1.

outcome(saved) :- saved.
outcome(steady) :- steady.
outcome(flopped) :- flopped.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        lines.append(asp.fact("sturdy", crop_id, crop.sturdy))
        lines.append(asp.fact("crop_fix", crop_id, crop.support_kind))
    for drink_id, drink in DRINKS.items():
        lines.append(asp.fact("drink", drink_id))
        lines.append(asp.fact("strength", drink_id, drink.strength))
        if drink.nourishing:
            lines.append(asp.fact("nourishing", drink_id))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        lines.append(asp.fact("amount", vessel_id, vessel.amount))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_kind", fix_id, fix.support_kind))
        lines.append(asp.fact("sense", fix_id, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_crop", params.crop),
            asp.fact("chosen_drink", params.drink),
            asp.fact("chosen_vessel", params.vessel),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases: list[StoryParams] = list(CURATED)
    for s in range(40):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
            cl = asp_outcome(params)
            if py != cl:
                bad += 1
        except StoryError as err:
            rc = 1
            print(f"ERROR while comparing outcomes for {params}: {err}")
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        _ = smoke.to_json()
        print("OK: smoke test generation and JSON serialization succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale garden story world with dot, drink, and rhyme. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--crop", choices=sorted(CROPS))
    ap.add_argument("--drink", choices=sorted(DRINKS))
    ap.add_argument("--vessel", choices=sorted(VESSELS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="delay before the grown-up helps")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.drink:
        drink = DRINKS[args.drink]
        if not good_drink(drink):
            raise StoryError(explain_drink(drink))
    if args.crop and args.fix:
        crop = CROPS[args.crop]
        fix = FIXES[args.fix]
        if not fix_fits(crop, fix):
            raise StoryError(explain_fix(crop, fix))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        crop = CROPS[args.crop] if args.crop else next(iter(CROPS.values()))
        raise StoryError(explain_fix(crop, FIXES[args.fix]))

    combos = [
        c for c in valid_combos()
        if (args.crop is None or c[0] == args.crop)
        and (args.drink is None or c[1] == args.drink)
        and (args.vessel is None or c[2] == args.vessel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crop_id, drink_id, vessel_id = rng.choice(sorted(combos))
    crop = CROPS[crop_id]

    fitting = [f.id for f in sensible_fixes() if fix_fits(crop, f)]
    if not fitting:
        raise StoryError("(No sensible fix fits the chosen crop.)")
    fix_id = args.fix or rng.choice(sorted(fitting))

    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        crop=crop_id,
        drink=drink_id,
        vessel=vessel_id,
        fix=fix_id,
        child_name=name,
        child_gender=gender,
        helper=helper,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop: {params.crop})")
    if params.drink not in DRINKS:
        raise StoryError(f"(Unknown drink: {params.drink})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    crop = CROPS[params.crop]
    drink = DRINKS[params.drink]
    vessel = VESSELS[params.vessel]
    fix = FIXES[params.fix]

    if not good_drink(drink):
        raise StoryError(explain_drink(drink))
    if not fix_fits(crop, fix):
        raise StoryError(explain_fix(crop, fix))

    world = tell(
        crop=crop,
        drink=drink,
        vessel=vessel,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
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
        print(f"{len(combos)} compatible (crop, drink, vessel) combos:\n")
        for crop, drink, vessel in combos:
            print(f"  {crop:10} {drink:12} {vessel}")
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
            header = f"### {p.child_name}: {p.crop} with {p.drink} from {p.vessel} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
