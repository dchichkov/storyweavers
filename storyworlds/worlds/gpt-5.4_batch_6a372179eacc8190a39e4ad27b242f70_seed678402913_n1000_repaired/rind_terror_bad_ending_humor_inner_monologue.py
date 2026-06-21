#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rind_terror_bad_ending_humor_inner_monologue.py
===========================================================================

A small folktale-flavored story world about a greedy trickster who tries to cross
water in a fruit rind to avoid paying a bridge toll. The world is intentionally
narrow: every reasonable story includes a rind, a moment of terror, comic inner
monologue, and a bad ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/rind_terror_bad_ending_humor_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/rind_terror_bad_ending_humor_inner_monologue.py --water duck_pond --rind watermelon --cargo cakes
    python storyworlds/worlds/gpt-5.4/rind_terror_bad_ending_humor_inner_monologue.py --rind orange
    python storyworlds/worlds/gpt-5.4/rind_terror_bad_ending_humor_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/rind_terror_bad_ending_humor_inner_monologue.py --verify
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
HERO_WEIGHT = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "girl", "woman", "mother"}
        male = {"fox", "jackal", "boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Water:
    id: str
    label: str
    phrase: str
    hazard: int
    birds: bool = False
    current: bool = False
    mudbank: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Rind:
    id: str
    label: str
    phrase: str
    capacity: int
    sturdy: int
    edible: bool = False
    splash: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    load: int
    desire: str
    spill: str
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


def _r_overload(world: World) -> list[str]:
    boat = world.get("boat")
    if boat.meters["launched"] < THRESHOLD:
        return []
    if boat.meters["overload"] < THRESHOLD:
        return []
    sig = ("overload",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["leaking"] += 1
    world.get("hero").memes["terror"] += 1
    return ["__overload__"]


def _r_birds_peck(world: World) -> list[str]:
    boat = world.get("boat")
    water = world.get("water")
    if boat.meters["launched"] < THRESHOLD:
        return []
    if water.attrs.get("birds") and boat.attrs.get("edible"):
        sig = ("peck",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        boat.meters["leaking"] += 1
        boat.meters["pecked"] += 1
        world.get("hero").memes["terror"] += 1
        return ["__pecked__"]
    return []


def _r_current_spin(world: World) -> list[str]:
    boat = world.get("boat")
    water = world.get("water")
    if boat.meters["launched"] < THRESHOLD:
        return []
    if not water.attrs.get("current"):
        return []
    sig = ("spin",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["spinning"] += 1
    world.get("hero").memes["terror"] += 1
    return ["__spinning__"]


def _r_sink(world: World) -> list[str]:
    boat = world.get("boat")
    hero = world.get("hero")
    cargo = world.get("cargo")
    if boat.meters["launched"] < THRESHOLD:
        return []
    should_sink = (
        boat.meters["leaking"] >= THRESHOLD
        or boat.meters["stability_fail"] >= THRESHOLD
    )
    if not should_sink:
        return []
    sig = ("sink",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["sunken"] += 1
    hero.meters["wet"] += 1
    hero.memes["terror"] += 1
    cargo.meters["lost"] += 1
    return ["__sunk__"]


def _r_lost_cargo(world: World) -> list[str]:
    boat = world.get("boat")
    cargo = world.get("cargo")
    if boat.meters["spinning"] < THRESHOLD or boat.meters["sunken"] >= THRESHOLD:
        return []
    sig = ("cargo_lost",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["lost"] += 1
    world.get("hero").memes["shame"] += 1
    return ["__lost__"]


CAUSAL_RULES = [
    Rule(name="overload", tag="physical", apply=_r_overload),
    Rule(name="birds_peck", tag="physical", apply=_r_birds_peck),
    Rule(name="current_spin", tag="physical", apply=_r_current_spin),
    Rule(name="sink", tag="physical", apply=_r_sink),
    Rule(name="lost_cargo", tag="social", apply=_r_lost_cargo),
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
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


def ride_plausible(rind: Rind, cargo: Cargo) -> bool:
    return rind.capacity >= HERO_WEIGHT + cargo.load


def stability_score(rind: Rind, cargo: Cargo, water: Water) -> int:
    return rind.sturdy - water.hazard - max(0, cargo.load - 1)


def outcome_of(params: "StoryParams") -> str:
    rind = RINDS[params.rind]
    cargo = CARGO[params.cargo]
    water = WATERS[params.water]
    if not ride_plausible(rind, cargo):
        raise StoryError(explain_rejection(rind, cargo))
    if water.birds and rind.edible:
        return "pecked"
    if stability_score(rind, cargo, water) <= -1:
        return "sunk"
    if water.current:
        return "spun"
    return "bogged"


def predict_crossing(world: World, water: Water, rind: Rind, cargo: Cargo) -> dict:
    sim = world.copy()
    boat = sim.get("boat")
    if not ride_plausible(rind, cargo):
        boat.meters["overload"] += 1
    if stability_score(rind, cargo, water) <= -1:
        boat.meters["stability_fail"] += 1
    boat.meters["launched"] += 1
    markers = propagate(sim, narrate=False)
    return {
        "sinks": sim.get("boat").meters["sunken"] >= THRESHOLD,
        "spins": sim.get("boat").meters["spinning"] >= THRESHOLD,
        "cargo_lost": sim.get("cargo").meters["lost"] >= THRESHOLD,
        "markers": markers,
    }


def introduce(world: World, hero: Entity, helper: Entity, cargo: Cargo, water: Water) -> None:
    hero.memes["greed"] += 1
    world.say(
        f"In the old days, when beasts bargained like peddlers and ponds listened like judges, "
        f"there lived a fox named {hero.id} beside {water.phrase}."
    )
    world.say(
        f"He had a trickster's tail, a quick mouth, and a nose set firmly on {cargo.desire}. "
        f"That morning he carried {cargo.phrase} and wished to cross without paying the bridge toll."
    )
    world.say(
        f"On the bank sat {helper.id} the {helper.type}, who was slow in step and quick in sense."
    )


def find_rind(world: World, hero: Entity, rind: Rind) -> None:
    boat = world.get("boat")
    hero.memes["pride"] += 1
    world.say(
        f"Then {hero.id} found {rind.phrase} by the reeds. It looked absurd enough to make even the wind grin."
    )
    world.say(
        f'"Why, this {rind.label} shall serve me as a lordly boat," thought {hero.id}. '
        f'"What is a bridge but a fee wearing planks?"'
    )
    boat.attrs["edible"] = rind.edible


def warn(world: World, helper: Entity, hero: Entity, water: Water, rind: Rind, cargo: Cargo) -> None:
    pred = predict_crossing(world, water, rind, cargo)
    world.facts["prediction"] = pred
    if pred["sinks"]:
        reason = "it would tip and gulp water"
    elif pred["spins"]:
        reason = "the current would seize it and turn it like a spoon in soup"
    else:
        reason = "it would not go where pride told it to go"
    world.say(
        f'{helper.id} looked once at the water and once at the rind and said, '
        f'"Friend fox, that craft is only a meal pretending to be a boat. {reason}."'
    )
    world.say(
        f"But {hero.id} only smiled the smile of someone who had already begun to admire himself."
    )


def launch(world: World, hero: Entity, water: Water, rind: Rind, cargo: Cargo) -> None:
    boat = world.get("boat")
    boat.meters["launched"] += 1
    if not ride_plausible(rind, cargo):
        boat.meters["overload"] += 1
    if stability_score(rind, cargo, water) <= -1:
        boat.meters["stability_fail"] += 1
    world.say(
        f"{hero.id} tucked {cargo.label} into the hollow of the rind, settled his narrow self inside it, "
        f"and pushed away from the bank with a twig far too grand for the job."
    )
    world.say(
        f'"See how wisely I travel," thought {hero.id}. "Soon they will tell stories of my genius and my dry paws."'
    )
    propagate(world, narrate=False)


def narrate_outcome(world: World, hero: Entity, helper: Entity, water: Water, rind: Rind, cargo: Cargo) -> None:
    outcome = outcome_of(world.facts["params"])
    if outcome == "pecked":
        world.say(
            f"But the ducks of {water.label} knew fruit when they saw it. They flapped over in a gossiping line "
            f"and pecked the sweet rind until little mouths of water opened all around {hero.id}."
        )
        world.say(
            f'"This is no voyage," thought {hero.id} in sudden terror. "This is breakfast, and I am sitting in the plate."'
        )
        world.say(
            f"Down went the rind. Up went the ducks. Away went {cargo.spill}, bobbing off while {hero.id} splashed for shore."
        )
        hero.meters["wet"] += 1
        hero.memes["terror"] += 1
        hero.memes["shame"] += 1
    elif outcome == "sunk":
        world.say(
            f"The water took one sniff at that plan and refused to respect it. The rind dipped, wobbled, "
            f"and folded under {hero.id} like a bad excuse."
        )
        world.say(
            f'"Oh, this is terror," thought {hero.id}. "I meant to float like a prince, not boil like a dumpling."'
        )
        world.say(
            f"In one cold gulp he vanished to the ears. {cargo.spill} slid free, and the current carried supper farther than his paws could reach."
        )
        hero.meters["wet"] += 1
        hero.memes["terror"] += 1
        hero.memes["shame"] += 1
    elif outcome == "spun":
        world.say(
            f"The current caught the rind and spun it round and round. {hero.id}'s tail stuck out on one side, "
            f"his nose on the other, and he looked less like a traveler than a turnip in a bowl."
        )
        world.say(
            f'"Steady now," thought {hero.id}, and then, as the world whirled, "No, not steady. Anything but steady. '
            f'This is terror wearing circles."'
        )
        world.say(
            f"He clutched at the air, lost hold of {cargo.label}, and drifted at last into the reeds, hungry, dizzy, and praised only by frogs."
        )
        hero.memes["terror"] += 1
        hero.memes["shame"] += 1
    else:
        world.say(
            f"For a little while the plan looked almost clever. That was the cruelest part."
        )
        world.say(
            f"The rind glided to the far side, kissed the mudbank, and stuck fast. {hero.id} sprang out with a flourish, "
            f"but the mud rose to his ankles and tugged {cargo.label} from his paws."
        )
        world.say(
            f'"If dignity has a sound," thought {hero.id}, "it is not this slurp." Terror fled, but shame sat down on my head."'
        )
        world.say(
            f"By the time he dragged himself free, {cargo.spill} was floating away, and children on the bridge were laughing hard enough to lean on the rails."
        )
        hero.memes["shame"] += 1
    world.para()
    world.say(
        f"{helper.id} did not laugh until {hero.id} was safely back on the bank. Then {helper.pronoun().capitalize()} said, "
        f'"A cheap crossing is often the dearest."'
    )
    world.say(
        f"So {hero.id} went home wet or muddy and certainly supperless, while the tale of the rind traveled farther than he did."
    )


def tell(water: Water, rind: Rind, cargo: Cargo, hero_name: str, helper_name: str, helper_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="fox", role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    water_ent = world.add(
        Entity(
            id="water",
            type="water",
            label=water.label,
            phrase=water.phrase,
            attrs={"hazard": water.hazard, "birds": water.birds, "current": water.current, "mudbank": water.mudbank},
            tags=set(water.tags),
        )
    )
    boat = world.add(
        Entity(
            id="boat",
            type="rind",
            label=rind.label,
            phrase=rind.phrase,
            attrs={"capacity": rind.capacity, "sturdy": rind.sturdy, "edible": rind.edible},
            tags=set(rind.tags),
        )
    )
    cargo_ent = world.add(
        Entity(
            id="cargo",
            type="cargo",
            label=cargo.label,
            phrase=cargo.phrase,
            attrs={"load": cargo.load},
            tags=set(cargo.tags),
        )
    )
    world.facts.update(hero=hero, helper=helper, water=water_ent, boat=boat, cargo=cargo_ent)

    introduce(world, hero, helper, cargo, water)
    world.para()
    find_rind(world, hero, rind)
    warn(world, helper, hero, water, rind, cargo)
    world.para()
    launch(world, hero, water, rind, cargo)
    narrate_outcome(world, hero, helper, water, rind, cargo)

    world.facts.update(
        water_cfg=water,
        rind_cfg=rind,
        cargo_cfg=cargo,
        outcome=outcome_of(world.facts["params"]),
        ruined=cargo_ent.meters["lost"] >= THRESHOLD or world.facts["params"].water in {"river_bend", "duck_pond", "mill_pond", "flood_creek"},
    )
    return world


WATERS = {
    "mill_pond": Water(
        id="mill_pond",
        label="the mill pond",
        phrase="the mill pond behind the flour mill",
        hazard=0,
        mudbank=True,
        tags={"pond", "mud"},
    ),
    "duck_pond": Water(
        id="duck_pond",
        label="the duck pond",
        phrase="the duck pond behind the willow trees",
        hazard=1,
        birds=True,
        mudbank=True,
        tags={"pond", "duck", "birds"},
    ),
    "river_bend": Water(
        id="river_bend",
        label="the river bend",
        phrase="the river bend where the water hurried past the stones",
        hazard=2,
        current=True,
        tags={"river", "current"},
    ),
    "flood_creek": Water(
        id="flood_creek",
        label="the flood creek",
        phrase="the flood creek swollen from last night's rain",
        hazard=3,
        current=True,
        tags={"river", "current", "flood"},
    ),
}

RINDS = {
    "pumpkin": Rind(
        id="pumpkin",
        label="pumpkin rind",
        phrase="a broad pumpkin rind, scraped hollow and shining orange",
        capacity=5,
        sturdy=3,
        edible=False,
        splash="thumped the water like a wooden bowl",
        tags={"rind", "pumpkin"},
    ),
    "watermelon": Rind(
        id="watermelon",
        label="watermelon rind",
        phrase="a half watermelon rind, green outside and pinkly tempting within",
        capacity=4,
        sturdy=1,
        edible=True,
        splash="kissed the water and wobbled",
        tags={"rind", "watermelon"},
    ),
    "melon": Rind(
        id="melon",
        label="melon rind",
        phrase="a pale melon rind that smelled far too much like lunch",
        capacity=3,
        sturdy=1,
        edible=True,
        splash="bobbed once like a hopeful turnip",
        tags={"rind", "melon"},
    ),
    "orange": Rind(
        id="orange",
        label="orange rind",
        phrase="a curled orange rind no wider than two foolish paws",
        capacity=1,
        sturdy=0,
        edible=True,
        splash="did not so much float as remember a puddle",
        tags={"rind", "orange"},
    ),
}

CARGO = {
    "cakes": Cargo(
        id="cakes",
        label="a basket of seed cakes",
        phrase="a basket of warm seed cakes for market",
        load=1,
        desire="seed cakes",
        spill="the cakes",
        tags={"cakes", "market"},
    ),
    "figs": Cargo(
        id="figs",
        label="a sack of figs",
        phrase="a sack of sticky figs tied with blue string",
        load=2,
        desire="sweet figs",
        spill="the figs",
        tags={"figs", "market"},
    ),
    "coins": Cargo(
        id="coins",
        label="a clay pot of coins",
        phrase="a clay pot of toll-money he hated to spend",
        load=3,
        desire="his own coins",
        spill="the pot and the coins",
        tags={"coins", "toll"},
    ),
}

HERO_NAMES = ["Siv", "Neri", "Taro", "Miko", "Perrin", "Rafi"]
HELPERS = {
    "tortoise": ["Old Shell", "Mossback", "Tavi"],
    "hen": ["Red Comb", "Hazel", "Pip"],
    "crow": ["Black Feather", "Croak", "Nettle"],
}


@dataclass
class StoryParams:
    water: str
    rind: str
    cargo: str
    hero_name: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        water="duck_pond",
        rind="watermelon",
        cargo="cakes",
        hero_name="Neri",
        helper_name="Old Shell",
        helper_type="tortoise",
    ),
    StoryParams(
        water="river_bend",
        rind="pumpkin",
        cargo="figs",
        hero_name="Siv",
        helper_name="Red Comb",
        helper_type="hen",
    ),
    StoryParams(
        water="flood_creek",
        rind="pumpkin",
        cargo="coins",
        hero_name="Taro",
        helper_name="Black Feather",
        helper_type="crow",
    ),
    StoryParams(
        water="mill_pond",
        rind="pumpkin",
        cargo="cakes",
        hero_name="Miko",
        helper_name="Hazel",
        helper_type="hen",
    ),
    StoryParams(
        water="river_bend",
        rind="melon",
        cargo="cakes",
        hero_name="Rafi",
        helper_name="Mossback",
        helper_type="tortoise",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for water_id in WATERS:
        for rind_id, rind in RINDS.items():
            for cargo_id, cargo in CARGO.items():
                if ride_plausible(rind, cargo):
                    combos.append((water_id, rind_id, cargo_id))
    return combos


def explain_rejection(rind: Rind, cargo: Cargo) -> str:
    need = HERO_WEIGHT + cargo.load
    return (
        f"(No story: a fox carrying {cargo.label} weighs about {need}, but the {rind.label} can only carry "
        f"{rind.capacity}. It is too small even for a foolish start.)"
    )


KNOWLEDGE = {
    "rind": [
        (
            "What is a rind?",
            "A rind is the tough outer skin of a fruit or vegetable. Some rinds are thick, but they are still not real boats."
        )
    ],
    "duck": [
        (
            "Why did the ducks peck the boat?",
            "Because an edible rind still smells like food to ducks. They were acting like ducks, even if it was terrible for the fox."
        )
    ],
    "current": [
        (
            "What is a current in a river?",
            "A current is water moving in one direction. It can push a floating thing where that thing did not mean to go."
        )
    ],
    "mud": [
        (
            "Why is a mudbank hard to walk on?",
            "Mud grips feet and paws and pulls them down. That is why a grand leap can turn into a slow, silly struggle."
        )
    ],
    "toll": [
        (
            "What is a toll?",
            "A toll is a price someone pays to use a bridge or road. In many old tales, a character tries to dodge the toll and learns a hard lesson."
        )
    ],
    "coins": [
        (
            "Why are coins heavy?",
            "Coins are made of metal, and metal is heavy for its size. A small pot of coins can weigh more than a basket of cakes."
        )
    ],
}
KNOWLEDGE_ORDER = ["rind", "duck", "current", "mud", "toll", "coins"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    water = f["water_cfg"]
    rind = f["rind_cfg"]
    cargo = f["cargo_cfg"]
    return [
        f'Write a short folk-tale style story that uses the words "rind" and "terror" and ends badly.',
        f"Tell a funny cautionary tale about a fox named {hero.id} who tries to cross {water.label} in {rind.phrase} to protect {cargo.label} and avoid a toll.",
        f"Write a folktale where {helper.id} warns {hero.id}, but the hero trusts an inner monologue more than good advice and loses {cargo.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    water = f["water_cfg"]
    rind = f["rind_cfg"]
    cargo = f["cargo_cfg"]
    outcome = f["outcome"]
    pred = f.get("prediction", {})
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the fox, who wanted a cheap crossing, and {helper.id} the {helper.type}, who tried to warn him."
        ),
        (
            f"Why did {hero.id} try to cross in a rind instead of using the bridge?",
            f"He did not want to pay the bridge toll. His greed made the ridiculous rind seem clever in his own mind."
        ),
        (
            f"What warning did {helper.id} give?",
            f"{helper.id} said the rind was not a real boat and would betray him on the water. The warning came from noticing what the water and the flimsy rind would do together."
        ),
    ]
    if pred:
        if pred.get("sinks"):
            qa.append(
                (
                    f"How did {helper.id} know the plan was dangerous?",
                    f"{helper.id} could see that the rind would not hold safely in that water. In the world model, the crossing would sink or fail almost at once, so the warning was honest."
                )
            )
        elif pred.get("spins"):
            qa.append(
                (
                    f"Why did {helper.id} think the current would matter?",
                    f"The current could grab a small floating thing and spin it away from the bank. That is why {helper.id} predicted trouble even before {hero.id} pushed off."
                )
            )
    if outcome == "pecked":
        qa.append(
            (
                f"What caused {hero.id}'s moment of terror?",
                f"The ducks pecked the edible rind because it still smelled like food. When the holes opened and water came in, his joke-boat stopped being a joke and became a danger."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended badly and foolishly: {hero.id} splashed back to shore, and {cargo.spill} floated away. He lost both his supper and his dignity."
            )
        )
    elif outcome == "sunk":
        qa.append(
            (
                f"What went wrong in the middle of the crossing?",
                f"The rind could not stay firm under the fox and his load, so it dipped and failed. He felt terror because the water punished his shortcut immediately."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {hero.id} soaked, hungry, and empty-pawed. The water took the cargo farther than he could follow."
            )
        )
    elif outcome == "spun":
        qa.append(
            (
                f"Why did {hero.id} lose {cargo.label}?",
                f"The current spun the rind until he could not keep hold of anything. His cargo slipped away because his foolish boat gave him no steady place to sit or brace himself."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"He reached only the reeds, not success. He was dizzy, ashamed, and still had nothing to eat or sell."
            )
        )
    else:
        qa.append(
            (
                f"Why was the ending still bad even though {hero.id} reached the far side?",
                f"He stuck in the mud and dropped {cargo.label} anyway. The trick seemed clever for one moment, but it still cost him what he wanted."
            )
        )
        qa.append(
            (
                "What changed by the last lines?",
                f"At first {hero.id} admired his own cleverness. By the end, the whole bridge was laughing and he had learned that looking clever is not the same as being wise."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rind", "toll"}
    water = world.facts["water_cfg"]
    cargo = world.facts["cargo_cfg"]
    tags |= set(water.tags)
    tags |= set(cargo.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
plausible(R, C) :- rind(R), cargo(C), capacity(R, Cap), hero_weight(H), load(C, L), Cap >= H + L.

outcome(W, R, C, pecked) :- water(W), rind(R), cargo(C), plausible(R, C), birds(W), edible(R).
outcome(W, R, C, sunk) :- water(W), rind(R), cargo(C), plausible(R, C),
                          not birds(W),
                          sturdy(R, S), hazard(W, H), load(C, L), S - H - (L - 1) <= -1.
outcome(W, R, C, spun) :- water(W), rind(R), cargo(C), plausible(R, C),
                          not outcome(W, R, C, pecked),
                          not outcome(W, R, C, sunk),
                          current(W).
outcome(W, R, C, bogged) :- water(W), rind(R), cargo(C), plausible(R, C),
                            not outcome(W, R, C, pecked),
                            not outcome(W, R, C, sunk),
                            not outcome(W, R, C, spun).

valid(W, R, C) :- water(W), rind(R), cargo(C), plausible(R, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("hero_weight", HERO_WEIGHT)]
    for wid, water in WATERS.items():
        lines.append(asp.fact("water", wid))
        lines.append(asp.fact("hazard", wid, water.hazard))
        if water.birds:
            lines.append(asp.fact("birds", wid))
        if water.current:
            lines.append(asp.fact("current", wid))
    for rid, rind in RINDS.items():
        lines.append(asp.fact("rind", rid))
        lines.append(asp.fact("capacity", rid, rind.capacity))
        lines.append(asp.fact("sturdy", rid, rind.sturdy))
        if rind.edible:
            lines.append(asp.fact("edible", rid))
    for cid, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("load", cid, cargo.load))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen", params.water, params.rind, params.cargo),
            f"want_outcome(X) :- chosen(W,R,C), outcome(W,R,C,X).",
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show want_outcome/1."))
    out = asp.atoms(model, "want_outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    for params in CURATED:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            rc = 1
            print(f"MISMATCH outcome for {params}: python={py} clingo={cl}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Empty story from smoke test.")
        print("OK: smoke-tested ordinary story generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folktale story world: a fox, a rind, comic terror, and a bad ending."
    )
    ap.add_argument("--water", choices=WATERS)
    ap.add_argument("--rind", choices=RINDS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--helper-type", choices=sorted(HELPERS))
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rind and args.cargo:
        rind = RINDS[args.rind]
        cargo = CARGO[args.cargo]
        if not ride_plausible(rind, cargo):
            raise StoryError(explain_rejection(rind, cargo))

    combos = [
        combo
        for combo in valid_combos()
        if (args.water is None or combo[0] == args.water)
        and (args.rind is None or combo[1] == args.rind)
        and (args.cargo is None or combo[2] == args.cargo)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    water, rind, cargo = rng.choice(sorted(combos))
    helper_type = args.helper_type or rng.choice(sorted(HELPERS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_pool = [name for name in HELPERS[helper_type] if name != hero_name]
    helper_name = args.helper_name or rng.choice(helper_pool)
    return StoryParams(
        water=water,
        rind=rind,
        cargo=cargo,
        hero_name=hero_name,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.water not in WATERS:
        raise StoryError(f"(Unknown water: {params.water})")
    if params.rind not in RINDS:
        raise StoryError(f"(Unknown rind: {params.rind})")
    if params.cargo not in CARGO:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")

    water = WATERS[params.water]
    rind = RINDS[params.rind]
    cargo = CARGO[params.cargo]
    if not ride_plausible(rind, cargo):
        raise StoryError(explain_rejection(rind, cargo))

    world = World()
    world.facts["params"] = params
    world = tell(water, rind, cargo, params.hero_name, params.helper_name, params.helper_type)
    world.facts["params"] = params

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
        print(asp_program("", "#show valid/3.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (water, rind, cargo) combos:\n")
        for water, rind, cargo in combos:
            p = StoryParams(
                water=water,
                rind=rind,
                cargo=cargo,
                hero_name="Siv",
                helper_name="Old Shell",
                helper_type="tortoise",
            )
            print(f"  {water:11} {rind:10} {cargo:6} -> {asp_outcome(p)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.hero_name}: {p.rind} on {p.water} carrying {p.cargo} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
