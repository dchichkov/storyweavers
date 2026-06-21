#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ineffable_busy_like_cautionary_slice_of_life.py
===========================================================================

A standalone storyworld about a child helping in a busy kitchen and nearly
touching something too hot with bare hands. The adult does not scold first; the
adult notices the real risk, stops the reach, and offers the right helper for
the specific hot dish.

Seed words carried into the rendered stories:
- ineffable
- busy
- like

The domain is slice-of-life and cautionary: ordinary family cooking, a small
moment of risk, a calm interruption, and a safer way to help.

Run it
------
python storyworlds/worlds/gpt-5.4/ineffable_busy_like_cautionary_slice_of_life.py
python storyworlds/worlds/gpt-5.4/ineffable_busy_like_cautionary_slice_of_life.py --dish soup --vessel pot
python storyworlds/worlds/gpt-5.4/ineffable_busy_like_cautionary_slice_of_life.py --vessel mixing_bowl
python storyworlds/worlds/gpt-5.4/ineffable_busy_like_cautionary_slice_of_life.py --all
python storyworlds/worlds/gpt-5.4/ineffable_busy_like_cautionary_slice_of_life.py --qa --json
python storyworlds/worlds/gpt-5.4/ineffable_busy_like_cautionary_slice_of_life.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Kitchen:
    id: str
    room_phrase: str
    table_phrase: str
    bustle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    aroma: str
    steam: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    hot_region: str
    carry_verb: str
    danger_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
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
        clone = World(self.kitchen)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_hot_reach(world: World) -> list[str]:
    hero = world.entities.get("hero")
    item = world.entities.get("item")
    if hero is None or item is None:
        return []
    if hero.memes["reaching"] < THRESHOLD:
        return []
    if item.meters["hot"] < THRESHOLD:
        return []
    if hero.meters["hands_protected"] >= THRESHOLD:
        return []
    sig = ("risk", hero.id, item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["burn_risk"] += 1
    hero.memes["alarm"] += 1
    return ["__risk__"]


CAUSAL_RULES = [
    Rule(name="hot_reach", tag="physical", apply=_r_hot_reach),
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
        for sent in produced:
            world.say(sent)
    return produced


KITCHENS = {
    "weeknight": Kitchen(
        id="weeknight",
        room_phrase="the kitchen",
        table_phrase="the little table by the window",
        bustle="The kitchen was busy with spoons clinking, cupboard doors tapping, and dinner almost ready.",
        tags={"kitchen", "busy"},
    ),
    "rainy_day": Kitchen(
        id="rainy_day",
        room_phrase="the warm kitchen",
        table_phrase="the round table near the rainy window",
        bustle="The kitchen felt busy in a soft way, with rain at the glass and supper coming together all at once.",
        tags={"kitchen", "busy"},
    ),
    "grandma_visit": Kitchen(
        id="grandma_visit",
        room_phrase="the family kitchen",
        table_phrase="the long table already set with napkins",
        bustle="The family kitchen was busy because company was coming, and every chair seemed to be waiting for someone.",
        tags={"kitchen", "busy"},
    ),
}

DISHES = {
    "soup": Dish(
        id="soup",
        label="soup",
        phrase="a pot of tomato soup",
        aroma="an ineffable cozy smell rose with the tomatoes and basil",
        steam="Steam curled up like a ribbon from the soup",
        tags={"soup", "hot_food", "ineffable"},
    ),
    "cocoa": Dish(
        id="cocoa",
        label="hot cocoa",
        phrase="a mug of hot cocoa",
        aroma="an ineffable chocolate smell filled the room",
        steam="A little cloud of steam floated up like a tiny ghost from the cocoa",
        tags={"cocoa", "hot_drink", "ineffable"},
    ),
    "oatmeal": Dish(
        id="oatmeal",
        label="oatmeal",
        phrase="a bowl of cinnamon oatmeal",
        aroma="an ineffable warm smell of cinnamon and oats drifted through the air",
        steam="The oatmeal puffed out steam like a sleepy dragon's breath",
        tags={"oatmeal", "hot_food", "ineffable"},
    ),
    "macaroni": Dish(
        id="macaroni",
        label="macaroni",
        phrase="a bubbling dish of macaroni",
        aroma="an ineffable cheesy smell made the whole room feel hungry",
        steam="The macaroni sent up steam like soft white threads",
        tags={"macaroni", "hot_food", "ineffable"},
    ),
}

VESSELS = {
    "pot": Vessel(
        id="pot",
        label="pot",
        phrase="the soup pot",
        hot_region="handles",
        carry_verb="carry it by the handles",
        danger_text="the metal handles could sting bare fingers",
        tags={"pot", "handles", "heat"},
    ),
    "mug": Vessel(
        id="mug",
        label="mug",
        phrase="the warm mug",
        hot_region="body",
        carry_verb="pick it up around the middle",
        danger_text="the sides were too hot for a small bare hand",
        tags={"mug", "body", "heat"},
    ),
    "bowl": Vessel(
        id="bowl",
        label="bowl",
        phrase="the deep bowl",
        hot_region="sides",
        carry_verb="lift it by the sides",
        danger_text="the hot bowl could nip little fingers",
        tags={"bowl", "sides", "heat"},
    ),
    "baking_dish": Vessel(
        id="baking_dish",
        label="baking dish",
        phrase="the baking dish",
        hot_region="sides",
        carry_verb="lift it from both sides",
        danger_text="the hot dish held oven heat in its sides",
        tags={"dish", "sides", "heat"},
    ),
    "mixing_bowl": Vessel(
        id="mixing_bowl",
        label="mixing bowl",
        phrase="the cool mixing bowl",
        hot_region="none",
        carry_verb="carry it to the table",
        danger_text="it was not hot at all",
        tags={"cool", "bowl"},
    ),
}

HELPERS = {
    "oven_mitts": Helper(
        id="oven_mitts",
        label="oven mitts",
        phrase="two puffy oven mitts",
        protects={"handles", "sides", "body"},
        tags={"mitts", "heat_safety"},
    ),
    "potholder": Helper(
        id="potholder",
        label="potholder",
        phrase="a thick potholder folded over small hands",
        protects={"handles", "sides"},
        tags={"potholder", "heat_safety"},
    ),
    "mug_sleeve": Helper(
        id="mug_sleeve",
        label="mug sleeve",
        phrase="a soft mug sleeve",
        protects={"body"},
        tags={"mug_sleeve", "heat_safety"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Zoe", "Ella", "Lucy", "Ruby"]
BOY_NAMES = ["Owen", "Leo", "Ben", "Max", "Theo", "Eli", "Sam", "Noah"]
TRAITS = ["helpful", "eager", "gentle", "curious", "careful", "bright"]


def vessel_is_hot(vessel: Vessel) -> bool:
    return vessel.hot_region != "none"


def select_helper(vessel: Vessel) -> Optional[Helper]:
    if not vessel_is_hot(vessel):
        return None
    for helper in HELPERS.values():
        if vessel.hot_region in helper.protects:
            return helper
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for kitchen_id in KITCHENS:
        for dish_id in DISHES:
            for vessel_id, vessel in VESSELS.items():
                if vessel_is_hot(vessel) and select_helper(vessel):
                    combos.append((kitchen_id, dish_id, vessel_id))
    return combos


def explain_rejection(vessel: Vessel) -> str:
    if not vessel_is_hot(vessel):
        return (
            f"(No story: {vessel.phrase} is not hot, so there is no honest burn warning. "
            f"This world only tells the near-burn story when the dish is truly hot.)"
        )
    return (
        f"(No story: nothing in the helper catalog safely protects the {vessel.hot_region} of "
        f"{vessel.phrase}. The fix must actually match the hot part.)"
    )


def predict_burn(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["reaching"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": hero.meters["burn_risk"] >= THRESHOLD,
        "alarm": hero.memes["alarm"],
    }


def introduce(world: World, hero: Entity, dish: Dish, vessel: Vessel) -> None:
    parent = world.get("parent")
    world.say(f"{hero.id} liked to help whenever {parent.pronoun('possessive')} {parent.label_word} cooked.")
    world.say(world.kitchen.bustle)
    world.say(f"On the stove sat {dish.phrase} in {vessel.phrase}, and {dish.aroma}.")
    world.say(f"{dish.steam}. {hero.id} thought it looked like dinner was making little signs in the air.")


def want_to_help(world: World, hero: Entity, dish: Dish, vessel: Vessel) -> None:
    hero.memes["helpfulness"] += 1
    world.say(
        f'"Can I bring it to {world.kitchen.table_phrase}?" {hero.id} asked. '
        f'{hero.pronoun().capitalize()} wanted to help because everything was busy and everyone was moving at once.'
    )
    world.say(
        f"{hero.id} stepped close and reached for {vessel.phrase}, ready to {vessel.carry_verb}."
    )


def warn(world: World, hero: Entity, vessel: Vessel) -> None:
    parent = world.get("parent")
    pred = predict_burn(world)
    world.facts["predicted_alarm"] = pred["alarm"]
    world.facts["predicted_risk"] = pred["risk"]
    if pred["risk"]:
        world.say(
            f'"Wait, sweetheart," {parent.label_word} said. "{vessel.danger_text.capitalize()}."'
        )


def intercept(world: World, hero: Entity) -> None:
    parent = world.get("parent")
    hero.memes["reaching"] += 1
    propagate(world, narrate=False)
    hero.memes["startled"] += 1
    parent.memes["protective"] += 1
    world.say(
        f"Before {hero.id}'s fingers touched, {parent.label_word} gently caught {hero.pronoun('possessive')} wrist."
    )
    if hero.meters["burn_risk"] >= THRESHOLD:
        world.say(
            f"It was only a near miss, but {hero.id} felt a quick flutter in {hero.pronoun('possessive')} chest."
        )


def explain_and_offer(world: World, hero: Entity, vessel: Vessel, helper: Helper) -> None:
    parent = world.get("parent")
    hero.memes["listening"] += 1
    world.say(
        f'"You are being helpful," {parent.label_word} said softly. "You just need the right thing for hot dishes."'
    )
    world.say(
        f'Then {parent.pronoun()} handed {hero.pronoun("object")} {helper.phrase}. '
        f'"These will protect your hands while you carry it."'
    )


def safe_carry(world: World, hero: Entity, dish: Dish, vessel: Vessel, helper: Helper) -> None:
    hero.meters["hands_protected"] += 1
    hero.memes["confidence"] += 1
    hero.memes["joy"] += 1
    hero.meters["helped"] += 1
    world.say(
        f"{hero.id} slid {hero.pronoun('possessive')} hands into the help, took hold of {vessel.phrase} again, and this time carried it carefully."
    )
    world.say(
        f"{hero.pronoun().capitalize()} set {dish.label} on {world.kitchen.table_phrase} without a spill or a sting."
    )


def ending(world: World, hero: Entity, dish: Dish, helper: Helper) -> None:
    parent = world.get("parent")
    hero.memes["pride"] += 1
    hero.memes["relief"] += 1
    parent.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} smiled. "See? Helpful and safe can go together."'
    )
    world.say(
        f"{hero.id} smiled too. The room was still busy, but now {hero.pronoun()} felt calm inside, and the warm {dish.label} on the table looked like a job done well."
    )
    world.say(
        f"After that, whenever something hot had to be moved, {hero.id} remembered to ask for {helper.label} first."
    )


def tell(
    kitchen: Kitchen,
    dish: Dish,
    vessel: Vessel,
    helper: Helper,
    *,
    name: str = "Lila",
    gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "helpful",
) -> World:
    world = World(kitchen)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, phrase=name, role="hero"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    item = world.add(Entity(id="item", kind="thing", type=vessel.label, label=vessel.label, phrase=vessel.phrase))
    hero.attrs["name"] = name
    hero.traits = {trait}
    item.meters["hot"] = 1.0

    introduce(world, hero, dish, vessel)
    world.para()
    want_to_help(world, hero, dish, vessel)
    warn(world, hero, vessel)
    intercept(world, hero)
    world.para()
    explain_and_offer(world, hero, vessel, helper)
    safe_carry(world, hero, dish, vessel, helper)
    ending(world, hero, dish, helper)

    world.facts.update(
        hero=hero,
        parent=parent,
        dish=dish,
        vessel=vessel,
        helper=helper,
        kitchen=kitchen,
        near_burn=hero.meters["burn_risk"] >= THRESHOLD,
        protected=hero.meters["hands_protected"] >= THRESHOLD,
        helped=hero.meters["helped"] >= THRESHOLD,
        name=name,
        trait=trait,
    )
    return world


@dataclass
class StoryParams:
    kitchen: str
    dish: str
    vessel: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "heat_safety": [
        (
            "Why can a hot pan or bowl hurt your hands?",
            "Very hot dishes can burn your skin because heat moves quickly into your fingers. Small hands need protection before touching something that just came from the stove or oven.",
        )
    ],
    "mitts": [
        (
            "What are oven mitts for?",
            "Oven mitts are thick covers for your hands. They help protect your skin when a grown-up lets you help with something hot.",
        )
    ],
    "potholder": [
        (
            "What does a potholder do?",
            "A potholder is a thick pad that helps block heat. It can make it safer to hold a hot handle or dish when a grown-up is helping.",
        )
    ],
    "mug_sleeve": [
        (
            "Why might a mug need a sleeve?",
            "A mug sleeve wraps around the outside of a hot mug. It helps your hand hold the mug without touching the hottest part.",
        )
    ],
    "soup": [
        (
            "Why does soup make steam?",
            "Soup makes steam when it is very warm and water rises into the air. Steam is a clue that the food may still be too hot to touch or eat right away.",
        )
    ],
    "cocoa": [
        (
            "Why should hot cocoa cool a little before a child carries it alone?",
            "Hot cocoa can spill and it can also be hot on the outside. Waiting or using help keeps little hands safer.",
        )
    ],
    "oatmeal": [
        (
            "Why can oatmeal stay hot for a long time?",
            "Thick foods like oatmeal hold heat inside them. Even when the top looks calm, the bowl and the food can still be very warm.",
        )
    ],
    "macaroni": [
        (
            "Why can baked macaroni stay hot after it leaves the oven?",
            "The pan and the food both hold heat. That means the sides can stay hot even after the bubbling slows down.",
        )
    ],
    "busy": [
        (
            "Why is it important to slow down when a room feels busy?",
            "When many things are happening at once, people can miss small dangers. Slowing down helps you notice heat, spills, and where your hands should go.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "busy",
    "heat_safety",
    "mitts",
    "potholder",
    "mug_sleeve",
    "soup",
    "cocoa",
    "oatmeal",
    "macaroni",
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    dish = world.facts["dish"]
    vessel = world.facts["vessel"]
    helper = world.facts["helper"]
    kitchen = world.facts["kitchen"]
    name = world.facts["name"]
    return [
        f'Write a slice-of-life cautionary story for a 3-to-5-year-old that includes the words "ineffable", "busy", and "like".',
        f"Tell a gentle kitchen story where {name} wants to help carry {dish.label} in {vessel.phrase}, but an adult notices the burn risk and offers {helper.label}.",
        f"Write a family story set in {kitchen.room_phrase} where a child learns that being helpful and being safe can go together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    dish = world.facts["dish"]
    vessel = world.facts["vessel"]
    helper = world.facts["helper"]
    kitchen = world.facts["kitchen"]
    name = world.facts["name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child who wanted to help in a busy family kitchen, and {name}'s {pw} who noticed a danger. The story stays small and ordinary, like a real supper-time moment at home.",
        ),
        (
            f"Why did {name} reach for the {vessel.label}?",
            f"{name} wanted to help bring the {dish.label} to {kitchen.table_phrase}. The room was busy, so helping felt important and grown-up.",
        ),
        (
            f"Why did {name}'s {pw} stop {hero.pronoun('object')}?",
            f"{name}'s {pw} saw that {vessel.danger_text}. That is why the reach was stopped before little fingers touched the hot part.",
        ),
    ]
    if world.facts["near_burn"]:
        qa.append(
            (
                f"Was anyone hurt when {name} tried to help?",
                f"No, nobody was hurt. It was only a near miss because {name}'s {pw} caught the moment in time and gently stopped the reach.",
            )
        )
    if world.facts["protected"] and world.facts["helped"]:
        qa.append(
            (
                f"How did {name} help safely in the end?",
                f"{name} used {helper.label} and then carried the hot {dish.label} carefully to the table. The helper matched the hot part of the {vessel.label}, so {name} could help without a burn.",
            )
        )
        qa.append(
            (
                "What changed by the end of the story?",
                f"At first, helping meant rushing toward something hot with bare hands. By the end, helping meant slowing down, using {helper.label}, and doing the same job safely.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"busy", "heat_safety"}
    tags |= set(world.facts["helper"].tags)
    tags |= set(world.facts["dish"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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


CURATED = [
    StoryParams(
        kitchen="weeknight",
        dish="soup",
        vessel="pot",
        name="Lila",
        gender="girl",
        parent="mother",
        trait="helpful",
    ),
    StoryParams(
        kitchen="rainy_day",
        dish="cocoa",
        vessel="mug",
        name="Owen",
        gender="boy",
        parent="father",
        trait="eager",
    ),
    StoryParams(
        kitchen="grandma_visit",
        dish="macaroni",
        vessel="baking_dish",
        name="Ruby",
        gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        kitchen="weeknight",
        dish="oatmeal",
        vessel="bowl",
        name="Theo",
        gender="boy",
        parent="father",
        trait="curious",
    ),
]


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
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hot(V) :- vessel(V), hot_region(V, R), R != none.
helper_fits(V, H) :- hot_region(V, R), protects(H, R).
valid(K, D, V) :- kitchen(K), dish(D), vessel(V), hot(V), helper_fits(V, _).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for kitchen_id in KITCHENS:
        lines.append(asp.fact("kitchen", kitchen_id))
    for dish_id in DISHES:
        lines.append(asp.fact("dish", dish_id))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        lines.append(asp.fact("hot_region", vessel_id, vessel.hot_region))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for region in sorted(helper.protects):
            lines.append(asp.fact("protects", helper_id, region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
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
        if not sample.story.strip():
            raise StoryError("Smoke test failed: empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child helps in a busy kitchen, reaches for something hot, and learns to ask for the right helper."
    )
    ap.add_argument("--kitchen", choices=KITCHENS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vessel:
        vessel = VESSELS[args.vessel]
        if not (vessel_is_hot(vessel) and select_helper(vessel)):
            raise StoryError(explain_rejection(vessel))

    combos = [
        combo
        for combo in valid_combos()
        if (args.kitchen is None or combo[0] == args.kitchen)
        and (args.dish is None or combo[1] == args.dish)
        and (args.vessel is None or combo[2] == args.vessel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    kitchen_id, dish_id, vessel_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        kitchen=kitchen_id,
        dish=dish_id,
        vessel=vessel_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.kitchen not in KITCHENS:
        raise StoryError(f"(Unknown kitchen: {params.kitchen})")
    if params.dish not in DISHES:
        raise StoryError(f"(Unknown dish: {params.dish})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")

    kitchen = KITCHENS[params.kitchen]
    dish = DISHES[params.dish]
    vessel = VESSELS[params.vessel]
    helper = select_helper(vessel)
    if helper is None:
        raise StoryError(explain_rejection(vessel))

    world = tell(
        kitchen=kitchen,
        dish=dish,
        vessel=vessel,
        helper=helper,
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (kitchen, dish, vessel) combos:\n")
        for kitchen_id, dish_id, vessel_id in combos:
            print(f"  {kitchen_id:12} {dish_id:10} {vessel_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
        for i, sample in enumerate(samples):
            sample.params.seed = base_seed + i
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
            header = f"### {p.name}: {p.dish} in {p.vessel} at {p.kitchen}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
