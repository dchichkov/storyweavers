#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wintry_lot_flashback_surprise_nursery_rhyme.py
=========================================================================

A standalone story world for a tiny nursery-rhyme-style tale set in a wintry
lot. A child finds a shivering small animal, remembers an old helping rhyme in a
flashback, chooses fitting food and shelter, and then a surprise ending proves
what changed.

Reasonableness constraint
-------------------------
This world refuses weak rescue logic. A story is only generated when:

* the chosen lot plausibly has that animal there, and
* the chosen food is the right food for that animal, and
* the chosen shelter is warm enough for that animal on a cold day.

That keeps the middle honest: the remembered rhyme can guide a real fix, and
the ending can show a believable rescue or reunion.

Run it
------
    python storyworlds/worlds/gpt-5.4/wintry_lot_flashback_surprise_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/wintry_lot_flashback_surprise_nursery_rhyme.py --animal rabbit --food tuna
    python storyworlds/worlds/gpt-5.4/wintry_lot_flashback_surprise_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/wintry_lot_flashback_surprise_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/wintry_lot_flashback_surprise_nursery_rhyme.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Lot:
    id: str
    phrase: str
    signs: str
    animals: set[str] = field(default_factory=set)
    surprise_hint: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Animal:
    id: str
    label: str
    phrase: str
    cry: str
    tracks: str
    food: str
    warmth_need: int
    nature: str
    surprise_kind: str
    surprise_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    for_animals: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Shelter:
    id: str
    label: str
    phrase: str
    warmth: int = 0
    make_text: str = ""
    settle_text: str = ""
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
    apply: Callable[[World], list[str]]


def _r_warm(world: World) -> list[str]:
    animal = world.get("animal")
    shelter = world.get("shelter") if "shelter" in world.entities else None
    if shelter is None or animal.meters["cold"] < THRESHOLD:
        return []
    sig = ("warm", shelter.id)
    if sig in world.fired:
        return []
    warmth = int(shelter.attrs.get("warmth", 0))
    need = int(animal.attrs.get("warmth_need", 0))
    if warmth < need:
        return []
    world.fired.add(sig)
    animal.meters["cold"] = 0.0
    animal.memes["calm"] += 1
    animal.memes["trust"] += 1
    return [shelter.attrs.get("settle_text", "")]


def _r_feed(world: World) -> list[str]:
    animal = world.get("animal")
    food = world.get("food") if "food" in world.entities else None
    if food is None or animal.meters["hungry"] < THRESHOLD:
        return []
    sig = ("feed", food.id)
    if sig in world.fired:
        return []
    if food.id not in animal.attrs.get("good_foods", set()):
        return []
    world.fired.add(sig)
    animal.meters["hungry"] = 0.0
    animal.memes["trust"] += 1
    return [f"The little {animal.label} nibbled and nibbled, then looked up with softer eyes."]


def _r_safe(world: World) -> list[str]:
    animal = world.get("animal")
    if animal.meters["cold"] >= THRESHOLD or animal.meters["hungry"] >= THRESHOLD:
        return []
    sig = ("safe", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["safe"] += 1
    return ["The small shiver faded. The tiny creature was safe enough to wait."]


CAUSAL_RULES = [
    Rule(name="warm", apply=_r_warm),
    Rule(name="feed", apply=_r_feed),
    Rule(name="safe", apply=_r_safe),
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
                produced.extend([s for s in sents if s])
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def animal_belongs_in_lot(lot: Lot, animal: Animal) -> bool:
    return animal.id in lot.animals


def food_fits(animal: Animal, food: Food) -> bool:
    return animal.id in food.for_animals and food.id == animal.food


def shelter_fits(animal: Animal, shelter: Shelter) -> bool:
    return shelter.warmth >= animal.warmth_need


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for lot_id, lot in LOTS.items():
        for animal_id, animal in ANIMALS.items():
            if not animal_belongs_in_lot(lot, animal):
                continue
            for food_id, food in FOODS.items():
                if not food_fits(animal, food):
                    continue
                for shelter_id, shelter in SHELTERS.items():
                    if shelter_fits(animal, shelter):
                        out.append((lot_id, animal_id, food_id, shelter_id))
    return out


def explain_rejection(lot: Lot, animal: Animal, food: Food, shelter: Shelter) -> str:
    if not animal_belongs_in_lot(lot, animal):
        return (f"(No story: {animal.phrase} is not a likely visitor in {lot.phrase}. "
                f"Pick an animal that fits that lot.)")
    if not food_fits(animal, food):
        return (f"(No story: {food.label} is not the right food for a {animal.label}. "
                f"This tale only allows a careful, fitting rescue.)")
    if not shelter_fits(animal, shelter):
        return (f"(No story: {shelter.label} is too chilly for a {animal.label} on a "
                f"wintry day. Pick a warmer shelter.)")
    return "(No story: this combination is not reasonable.)"


def predict_rescue(world: World, food_id: str, shelter_id: str) -> dict:
    sim = world.copy()
    sim.add(Entity(id="food", label=FOODS[food_id].label))
    sim.add(Entity(
        id="shelter",
        label=SHELTERS[shelter_id].label,
        attrs={"warmth": SHELTERS[shelter_id].warmth, "settle_text": SHELTERS[shelter_id].settle_text},
    ))
    propagate(sim, narrate=False)
    animal = sim.get("animal")
    return {
        "safe": animal.meters["safe"] >= THRESHOLD,
        "trust": animal.memes["trust"],
        "cold": animal.meters["cold"],
        "hungry": animal.meters["hungry"],
    }


def rhyme_lines(animal: Animal, food: Food) -> tuple[str, str]:
    first = "Soft feet, slow feet, hush the snow-white beat."
    second = f"Ask what little mouths may eat; {food.label} makes the helping sweet."
    if animal.id == "rabbit":
        second = "Ask what little mouths may eat; a carrot keeps the kindness neat."
    elif animal.id == "kitten":
        second = "Ask what little mouths may eat; warm fish makes the helping sweet."
    elif animal.id == "puppy":
        second = "Ask what little mouths may eat; kind dry bites are good to greet."
    return first, second


def introduce(world: World, child: Entity, parent: Entity, lot: Lot) -> None:
    world.say(
        f"In a wintry lot, where the pale wind played, {child.id} and {child.pronoun('possessive')} "
        f"{parent.label_word} went by {lot.phrase}. {lot.signs}"
    )


def hear_cry(world: World, child: Entity, animal: Animal, lot: Lot) -> None:
    child.memes["care"] += 1
    world.say(
        f"From a snowy corner came {animal.cry}, small as a button bell. "
        f"There, by {lot.surprise_hint}, huddled {animal.phrase}."
    )
    world.say(f"{child.id} saw {animal.tracks} and stopped with a mitten on {child.pronoun('possessive')} heart.")


def flashback(world: World, child: Entity, granny_name: str, animal: Animal, food: Food) -> None:
    child.memes["memory"] += 1
    line1, line2 = rhyme_lines(animal, food)
    world.say(
        f"Then back in {child.pronoun('possessive')} mind came a flashback, bright as a candle in the dusk."
    )
    world.say(
        f"Last winter, {granny_name} had tapped the table and sung, "
        f'"{line1} {line2}"'
    )


def choose_help(world: World, child: Entity, parent: Entity, food: Food, shelter: Shelter) -> None:
    world.add(Entity(id="food", label=food.label, phrase=food.phrase, tags=set(food.tags)))
    world.add(Entity(
        id="shelter",
        label=shelter.label,
        phrase=shelter.phrase,
        attrs={"warmth": shelter.warmth, "settle_text": shelter.settle_text},
        tags=set(shelter.tags),
    ))
    world.say(
        f'"May we help the tiny thing the careful way?" asked {child.id}.'
    )
    world.say(
        f'{parent.label_word.capitalize()} nodded. Together they brought {food.phrase}, and they {shelter.make_text}.'
    )


def settle(world: World, animal_ent: Entity) -> None:
    animal_ent.memes["hope"] += 1
    propagate(world, narrate=True)


def call_help(world: World, parent: Entity, animal: Animal) -> None:
    world.say(
        f'Then {parent.label_word} used the phone and called for help, because small lives need grown-up hands as well.'
    )
    if animal.nature == "pet":
        world.say("A number on a collar tag gave the next clue.")
    else:
        world.say("They waited quietly, so the shy place around the lot could answer back.")


def surprise(world: World, child: Entity, parent: Entity, animal: Animal) -> None:
    animal_ent = world.get("animal")
    animal_ent.memes["joy"] += 1
    child.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.say(
        f"Then came the surprise: {animal.surprise_text}"
    )
    if animal.surprise_kind == "owner":
        world.say(
            f"{child.id} laughed to see the little one lifted into warm arms at last."
        )
    else:
        world.say(
            f"{child.id} stood still and smiling, for the lot was not lonely after all."
        )


def ending(world: World, child: Entity, parent: Entity, lot: Lot, animal: Animal) -> None:
    world.say(
        f"Home they went through the wintry light, and {child.id} softly kept the rhyme. "
        f"In {lot.phrase}, kindness had made a colder morning kind."
    )
    world.facts["ending_image"] = (
        f"{child.id} walking home with the rhyme in mind while the surprise in {lot.phrase} stayed warm behind."
    )


def tell(
    lot: Lot,
    animal: Animal,
    food: Food,
    shelter: Shelter,
    *,
    child_name: str = "Molly",
    child_gender: str = "girl",
    parent_type: str = "mother",
    child_trait: str = "gentle",
    granny_name: str = "Gran",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[child_trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    animal_ent = world.add(Entity(
        id="animal",
        type="animal",
        label=animal.label,
        phrase=animal.phrase,
        role="animal",
        attrs={"warmth_need": animal.warmth_need, "good_foods": {animal.food}},
        tags=set(animal.tags),
    ))
    animal_ent.meters["cold"] = 1.0
    animal_ent.meters["hungry"] = 1.0
    animal_ent.memes["fear"] = 1.0

    introduce(world, child, parent, lot)
    hear_cry(world, child, animal, lot)

    world.para()
    flashback(world, child, granny_name, animal, food)
    pred = predict_rescue(world, food.id, shelter.id)
    world.facts["predicted_safe"] = pred["safe"]
    world.facts["predicted_trust"] = pred["trust"]
    choose_help(world, child, parent, food, shelter)

    world.para()
    settle(world, animal_ent)
    call_help(world, parent, animal)
    surprise(world, child, parent, animal)

    world.para()
    ending(world, child, parent, lot, animal)

    world.facts.update(
        child=child,
        parent=parent,
        animal_cfg=animal,
        animal=animal_ent,
        lot=lot,
        food=food,
        shelter=shelter,
        granny_name=granny_name,
        safe=animal_ent.meters["safe"] >= THRESHOLD,
        surprise_kind=animal.surprise_kind,
    )
    return world


LOTS = {
    "bakery_lot": Lot(
        id="bakery_lot",
        phrase="the little bakery lot",
        signs="Floury footprints crossed the fence, and the bins gave off a warm bread smell.",
        animals={"kitten", "rabbit"},
        surprise_hint="the stack of flour crates",
        tags={"lot", "winter"},
    ),
    "market_lot": Lot(
        id="market_lot",
        phrase="the market lot",
        signs="Snow squeaked under boots, and old carts stood in a silver row.",
        animals={"puppy", "kitten"},
        surprise_hint="the quiet cart wheel",
        tags={"lot", "winter"},
    ),
    "chapel_lot": Lot(
        id="chapel_lot",
        phrase="the chapel lot",
        signs="Bare hedges stitched the edge, and the bell house watched the snow.",
        animals={"rabbit", "kitten"},
        surprise_hint="the hedge by the low stone wall",
        tags={"lot", "winter"},
    ),
}

ANIMALS = {
    "kitten": Animal(
        id="kitten",
        label="kitten",
        phrase="a soot-gray kitten with a blue ribbon collar",
        cry="a mew-mew, thin and true",
        tracks="tiny comma tracks in the frost",
        food="tuna",
        warmth_need=2,
        nature="pet",
        surprise_kind="owner",
        surprise_text="a baker's daughter came running with a scarf flying behind her, crying, "
                      '"Button! Button!" The kitten answered with one bright mew.',
        tags={"kitten", "pet", "winter_help"},
    ),
    "puppy": Animal(
        id="puppy",
        label="puppy",
        phrase="a brown puppy with one white paw and a red tag",
        cry="a yip-yip under the wind",
        tracks="round puppy prints in the powdery snow",
        food="kibble",
        warmth_need=2,
        nature="pet",
        surprise_kind="owner",
        surprise_text="a shopkeeper hurried over when the phone rang, and the puppy tumbled into his boots, "
                      "wagging like a broom of joy",
        tags={"puppy", "pet", "winter_help"},
    ),
    "rabbit": Animal(
        id="rabbit",
        label="rabbit",
        phrase="a snow-dusted rabbit with whiskers like threads",
        cry="the faintest rustle and nibble in the grass",
        tracks="two neat hopping marks near the hedge",
        food="carrot",
        warmth_need=1,
        nature="wild",
        surprise_kind="family",
        surprise_text="two more rabbits popped from the hedge like gray pebbles come alive, "
                      "and all three noses twitched at once",
        tags={"rabbit", "wildlife", "winter_help"},
    ),
}

FOODS = {
    "tuna": Food(
        id="tuna",
        label="tuna",
        phrase="a little dish of tuna",
        for_animals={"kitten"},
        tags={"fish_food"},
    ),
    "kibble": Food(
        id="kibble",
        label="kibble",
        phrase="a small scoop of puppy kibble",
        for_animals={"puppy"},
        tags={"dog_food"},
    ),
    "carrot": Food(
        id="carrot",
        label="carrot",
        phrase="a few sweet carrot coins",
        for_animals={"rabbit"},
        tags={"rabbit_food"},
    ),
    "bread": Food(
        id="bread",
        label="bread",
        phrase="a crust of bread",
        for_animals=set(),
        tags={"bread"},
    ),
}

SHELTERS = {
    "basket_blanket": Shelter(
        id="basket_blanket",
        label="basket with a blanket",
        phrase="a basket with a wool blanket",
        warmth=2,
        make_text="made a basket with a blanket under the dry eaves",
        settle_text="Curled in the basket, the little body stopped trembling so hard.",
        tags={"warm_shelter"},
    ),
    "coat_tent": Shelter(
        id="coat_tent",
        label="coat tent",
        phrase="a coat tent by the wall",
        warmth=1,
        make_text="propped up a coat tent by the wall to break the wind",
        settle_text="Under the coat tent, the tiny creature tucked in from the wind.",
        tags={"warm_shelter"},
    ),
    "crate_bed": Shelter(
        id="crate_bed",
        label="crate bed",
        phrase="a wooden crate bed lined with a towel",
        warmth=2,
        make_text="lined a wooden crate bed with a towel near the fence",
        settle_text="Inside the crate bed, the small one blinked and went still in the best way.",
        tags={"warm_shelter"},
    ),
}


GIRL_NAMES = ["Molly", "Nell", "Daisy", "Rosie", "May", "Tilly", "Elsie"]
BOY_NAMES = ["Toby", "Ned", "Finn", "Ollie", "Sam", "Ben", "Milo"]
TRAITS = ["gentle", "bright", "patient", "kind", "careful"]


@dataclass
class StoryParams:
    lot: str
    animal: str
    food: str
    shelter: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    granny_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "lot": [(
        "What is a lot?",
        "A lot is an open piece of ground, like a parking lot or empty patch by buildings. In winter it can feel wide, cold, and windy."
    )],
    "winter": [(
        "Why do small animals need extra help in winter?",
        "Cold weather makes it harder for small animals to stay warm and find food. A sheltered place and the right food can help them until a grown-up rescuer comes."
    )],
    "kitten": [(
        "Why should a lost kitten be kept warm?",
        "A tiny kitten loses body heat quickly in cold weather. Warmth helps it stop shaking and keeps it safer while grown-ups look for its home."
    )],
    "puppy": [(
        "Why is a collar tag helpful?",
        "A collar tag can tell grown-ups who the puppy belongs to. That makes it easier to help the puppy get home."
    )],
    "rabbit": [(
        "Why should people stay quiet around a wild rabbit?",
        "Wild rabbits scare easily. Quiet, gentle waiting helps them feel safe enough to come out or move on."
    )],
    "fish_food": [(
        "Why was tuna a good choice for the kitten?",
        "The story world treats tuna as food that suits the kitten. The child remembered to ask what the little mouth could safely eat before offering help."
    )],
    "dog_food": [(
        "What is kibble?",
        "Kibble is dry dog food made in small crunchy pieces. It is easy for a puppy to nibble."
    )],
    "rabbit_food": [(
        "Why was carrot used for the rabbit?",
        "The remembered rhyme tells the child to choose food that fits the animal. In this little world, carrot is the careful choice for the rabbit."
    )],
    "warm_shelter": [(
        "Why does a shelter help on a snowy day?",
        "A shelter blocks the wind and holds in more warmth. That gives a cold little animal a safer place to rest."
    )],
}
KNOWLEDGE_ORDER = [
    "lot", "winter", "kitten", "puppy", "rabbit",
    "fish_food", "dog_food", "rabbit_food", "warm_shelter",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    animal = f["animal_cfg"]
    lot = f["lot"]
    food = f["food"]
    return [
        f'Write a short nursery-rhyme-style story that includes the words "wintry" and "lot". '
        f'Use a flashback and end with a surprise.',
        f"Tell a gentle story about {child.id} finding {animal.phrase} in {lot.phrase}, "
        f"remembering an old rhyme, and choosing {food.label} to help.",
        f"Write a child-facing winter story in singsong language where a careful memory guides "
        f"a rescue in a snowy lot and the ending reveals a happy surprise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    animal = f["animal_cfg"]
    lot = f["lot"]
    food = f["food"]
    shelter = f["shelter"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and {animal.phrase} in {lot.phrase}. "
            f"They meet on a cold day when the little animal needs help."
        ),
        (
            f"Where did {child.id} find the {animal.label}?",
            f"{child.id} found the {animal.label} in {lot.phrase}, near {lot.surprise_hint}. "
            f"The snowy, windy place made the animal seem even smaller and colder."
        ),
        (
            "What was the flashback about?",
            f"The flashback was a memory of {f['granny_name']} singing a helping rhyme from last winter. "
            f"The rhyme reminded {child.id} to choose food that fit the little animal instead of guessing."
        ),
        (
            f"How did {child.id} help the {animal.label}?",
            f"{child.id} and {parent.label_word} brought {food.phrase} and made {shelter.phrase}. "
            f"That gave the shivering animal the right food and a warmer place to wait."
        ),
    ]
    if f.get("safe"):
        qa.append((
            f"Why did the plan work?",
            f"It worked because the food matched the {animal.label} and the shelter was warm enough for a wintry day. "
            f"After that, the small shiver faded and the animal could rest safely."
        ))
    if f["surprise_kind"] == "owner":
        qa.append((
            "What was the surprise at the end?",
            f"The surprise was that the little animal belonged to someone nearby, and that person came running when help was called. "
            f"The reunion showed that the careful rescue gave the pet time to get home."
        ))
    else:
        qa.append((
            "What was the surprise at the end?",
            f"The surprise was that the rabbit was not alone at all. "
            f"When it felt safer, two more rabbits came out from the hedge."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"lot", "winter", "warm_shelter"}
    tags |= set(f["animal_cfg"].tags)
    tags |= set(f["food"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        lot="bakery_lot",
        animal="kitten",
        food="tuna",
        shelter="basket_blanket",
        child_name="Molly",
        child_gender="girl",
        parent="mother",
        trait="gentle",
        granny_name="Gran",
    ),
    StoryParams(
        lot="market_lot",
        animal="puppy",
        food="kibble",
        shelter="crate_bed",
        child_name="Toby",
        child_gender="boy",
        parent="father",
        trait="kind",
        granny_name="Nana",
    ),
    StoryParams(
        lot="chapel_lot",
        animal="rabbit",
        food="carrot",
        shelter="coat_tent",
        child_name="Elsie",
        child_gender="girl",
        parent="mother",
        trait="patient",
        granny_name="Gran",
    ),
    StoryParams(
        lot="bakery_lot",
        animal="rabbit",
        food="carrot",
        shelter="basket_blanket",
        child_name="Finn",
        child_gender="boy",
        parent="father",
        trait="careful",
        granny_name="Nana",
    ),
]


ASP_RULES = r"""
belongs_in(L, A) :- lot(L), animal(A), lot_has(L, A).
fits_food(A, F) :- animal(A), food(F), right_food(A, F).
warm_enough(A, S) :- animal(A), shelter(S), warmth_need(A, N), shelter_warmth(S, W), W >= N.
valid(L, A, F, S) :- belongs_in(L, A), fits_food(A, F), warm_enough(A, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lot_id, lot in LOTS.items():
        lines.append(asp.fact("lot", lot_id))
        for animal_id in sorted(lot.animals):
            lines.append(asp.fact("lot_has", lot_id, animal_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("warmth_need", animal_id, animal.warmth_need))
        lines.append(asp.fact("right_food", animal_id, animal.food))
    for food_id in FOODS:
        lines.append(asp.fact("food", food_id))
    for shelter_id, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", shelter_id))
        lines.append(asp.fact("shelter_warmth", shelter_id, shelter.warmth))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "wintry" not in sample.story or "surprise" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missed a required beat.)")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme-style winter rescue in a lot. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--lot", choices=LOTS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lot and args.animal and args.food and args.shelter:
        lot = LOTS[args.lot]
        animal = ANIMALS[args.animal]
        food = FOODS[args.food]
        shelter = SHELTERS[args.shelter]
        if (args.lot, args.animal, args.food, args.shelter) not in set(valid_combos()):
            raise StoryError(explain_rejection(lot, animal, food, shelter))
    elif args.lot and args.animal and not animal_belongs_in_lot(LOTS[args.lot], ANIMALS[args.animal]):
        raise StoryError(explain_rejection(LOTS[args.lot], ANIMALS[args.animal], FOODS["bread"], SHELTERS["coat_tent"]))
    elif args.animal and args.food and not food_fits(ANIMALS[args.animal], FOODS[args.food]):
        raise StoryError(explain_rejection(next(iter(LOTS.values())), ANIMALS[args.animal], FOODS[args.food], SHELTERS["basket_blanket"]))
    elif args.animal and args.shelter and not shelter_fits(ANIMALS[args.animal], SHELTERS[args.shelter]):
        raise StoryError(explain_rejection(next(iter(LOTS.values())), ANIMALS[args.animal], FOODS[ANIMALS[args.animal].food], SHELTERS[args.shelter]))

    combos = [
        combo for combo in valid_combos()
        if (args.lot is None or combo[0] == args.lot)
        and (args.animal is None or combo[1] == args.animal)
        and (args.food is None or combo[2] == args.food)
        and (args.shelter is None or combo[3] == args.shelter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lot_id, animal_id, food_id, shelter_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    granny_name = rng.choice(["Gran", "Nana", "Granny May"])
    return StoryParams(
        lot=lot_id,
        animal=animal_id,
        food=food_id,
        shelter=shelter_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        granny_name=granny_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.lot not in LOTS:
        raise StoryError(f"(Unknown lot: {params.lot})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.shelter not in SHELTERS:
        raise StoryError(f"(Unknown shelter: {params.shelter})")
    if (params.lot, params.animal, params.food, params.shelter) not in set(valid_combos()):
        raise StoryError(explain_rejection(
            LOTS[params.lot], ANIMALS[params.animal], FOODS[params.food], SHELTERS[params.shelter]
        ))

    world = tell(
        LOTS[params.lot],
        ANIMALS[params.animal],
        FOODS[params.food],
        SHELTERS[params.shelter],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        child_trait=params.trait,
        granny_name=params.granny_name,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lot, animal, food, shelter) combos:\n")
        for lot_id, animal_id, food_id, shelter_id in combos:
            print(f"  {lot_id:11} {animal_id:7} {food_id:7} {shelter_id}")
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
            header = f"### {p.child_name}: {p.animal} in {p.lot} ({p.food}, {p.shelter})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
