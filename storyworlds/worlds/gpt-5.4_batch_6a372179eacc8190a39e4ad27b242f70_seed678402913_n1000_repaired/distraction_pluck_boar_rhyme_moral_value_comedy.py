#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/distraction_pluck_boar_rhyme_moral_value_comedy.py
==============================================================================

A small storyworld about a child using pluck, a silly rhyme, and a good
distraction to guide a wandering boar away from a busy gathering. The tone stays
comic and child-facing: the boar is rude and muddy, never monstrous, and the
ending proves a moral about brave, thoughtful help.

Run it
------
    python storyworlds/worlds/gpt-5.4/distraction_pluck_boar_rhyme_moral_value_comedy.py
    python storyworlds/worlds/gpt-5.4/distraction_pluck_boar_rhyme_moral_value_comedy.py --place fair --bait apples
    python storyworlds/worlds/gpt-5.4/distraction_pluck_boar_rhyme_moral_value_comedy.py --bait marbles
    python storyworlds/worlds/gpt-5.4/distraction_pluck_boar_rhyme_moral_value_comedy.py --all
    python storyworlds/worlds/gpt-5.4/distraction_pluck_boar_rhyme_moral_value_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/distraction_pluck_boar_rhyme_moral_value_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/distraction_pluck_boar_rhyme_moral_value_comedy.py --verify
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
PLUCK_BRAVE = 5
RHYME_HELP = 1


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "gardener"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    crowd: str
    treat: str
    path: str
    pen: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BoarType:
    id: str
    label: str
    entry: str
    muddy: str
    appetite: set[str] = field(default_factory=set)
    speed: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Bait:
    id: str
    label: str
    phrase: str
    scent: str
    kind: str
    silly: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperType:
    id: str
    label: str
    type: str
    tool: str
    close_method: str
    delay: int
    tags: set[str] = field(default_factory=set)


@dataclass
class RhymeStyle:
    id: str
    opening: str
    chant_a: str
    chant_b: str
    effect: str
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    boar = world.get("boar")
    crowd = world.get("crowd")
    if boar.meters["loose"] < THRESHOLD:
        return []
    sig = ("alarm", "crowd")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.memes["alarm"] += 1
    hero = world.get("hero")
    hero.memes["concern"] += 1
    return ["__alarm__"]


def _r_follow(world: World) -> list[str]:
    boar = world.get("boar")
    if boar.memes["tempted"] < THRESHOLD:
        return []
    sig = ("follow", "boar")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boar.meters["moving_to_gate"] += 1
    return ["__follow__"]


def _r_gate(world: World) -> list[str]:
    boar = world.get("boar")
    helper = world.get("helper")
    if boar.meters["moving_to_gate"] < THRESHOLD or helper.meters["ready"] < THRESHOLD:
        return []
    sig = ("gate", "boar")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boar.meters["loose"] = 0.0
    boar.meters["safe"] += 1
    crowd = world.get("crowd")
    crowd.memes["relief"] += 1
    return ["__safe__"]


CAUSAL_RULES = [
    Rule(name="alarm", tag="social", apply=_r_alarm),
    Rule(name="follow", tag="physical", apply=_r_follow),
    Rule(name="gate", tag="physical", apply=_r_gate),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    return produced


def bait_works(boar_cfg: BoarType, bait_cfg: Bait) -> bool:
    return bait_cfg.safe and bait_cfg.kind in boar_cfg.appetite


def helper_sensible(helper_cfg: HelperType) -> bool:
    return helper_cfg.delay <= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for boar_id, boar in BOARS.items():
            for bait_id, bait in BAITS.items():
                if bait_works(boar, bait):
                    combos.append((place_id, boar_id, bait_id))
    return combos


def pluck_score(trait: str) -> int:
    return {"timid": 2, "careful": 4, "bold": 5, "cheerful": 4, "brisk": 5, "steady": 5}.get(trait, 4)


def rhyme_score(style_id: str) -> int:
    return {"bouncy": 1, "clappy": 1, "marching": 1}.get(style_id, 1)


def outcome_of(params: "StoryParams") -> str:
    if params.place not in PLACES or params.boar not in BOARS or params.bait not in BAITS:
        raise StoryError("(Invalid params: unknown place, boar, or bait.)")
    if params.helper not in HELPERS or params.rhyme not in RHYMES:
        raise StoryError("(Invalid params: unknown helper or rhyme.)")
    boar = BOARS[params.boar]
    bait = BAITS[params.bait]
    helper = HELPERS[params.helper]
    if not bait_works(boar, bait):
        raise StoryError(explain_rejection(boar, bait))
    if not helper_sensible(helper):
        raise StoryError(explain_helper(helper.id))
    courage = pluck_score(params.trait)
    rhythm = rhyme_score(params.rhyme)
    control = courage + rhythm
    difficulty = boar.speed + helper.delay
    return "tidy" if control >= difficulty + 1 else "messy"


def predict_distraction(world: World, bait_cfg: Bait, helper_cfg: HelperType) -> dict:
    sim = world.copy()
    boar = sim.get("boar")
    helper = sim.get("helper")
    boar.meters["loose"] += 1
    boar.memes["tempted"] += 1
    helper.meters["ready"] += 1 if helper_cfg.delay <= 1 else 0
    propagate(sim, narrate=False)
    return {
        "boar_moves": sim.get("boar").meters["moving_to_gate"] >= THRESHOLD,
        "helper_ready": sim.get("helper").meters["ready"] >= THRESHOLD,
    }


def setup_scene(world: World, place_cfg: Place, hero: Entity, friend: Entity, crowd: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On market morning, {hero.id} and {friend.id} hurried into {place_cfg.label}, where "
        f"{place_cfg.crowd} and the smell of {place_cfg.treat} floated through the air."
    )
    world.say(
        f"{hero.id} was supposed to stand on a crate and say a silly rhyme for the neighbors. "
        f"{friend.id} carried the bell for the clapping part."
    )


def boar_enters(world: World, boar_cfg: BoarType, crowd: Entity) -> None:
    boar = world.get("boar")
    boar.meters["loose"] += 1
    crowd.memes["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {boar_cfg.entry}. A {boar_cfg.label} trotted straight between the tables, "
        f"{boar_cfg.muddy}, and everyone forgot the rhyme at once."
    )


def worry(world: World, hero: Entity, friend: Entity, place_cfg: Place) -> None:
    hero.memes["concern"] += 1
    friend.memes["concern"] += 1
    world.say(
        f'"Oh dear," said {friend.id}. "If that boar reaches {place_cfg.treat}, the whole place will turn into a pancake storm."'
    )
    world.say(
        f"{hero.id} felt a jump in {hero.pronoun('possessive')} chest. It was not exactly fear and not exactly excitement. "
        f"It was the sort of pluck that makes your knees wobble while your feet still step forward."
    )


def choose_plan(world: World, hero: Entity, friend: Entity, bait_cfg: Bait, helper_cfg: HelperType, rhyme_cfg: RhymeStyle) -> None:
    pred = predict_distraction(world, bait_cfg, helper_cfg)
    world.facts["pred_boar_moves"] = pred["boar_moves"]
    world.facts["pred_helper_ready"] = pred["helper_ready"]
    world.say(
        f'"I can make a distraction," said {hero.id}. "{rhyme_cfg.opening}" '
        f'{friend.id} blinked, then looked at {bait_cfg.phrase}.'
    )
    world.say(
        f'"You rhyme. I run for {helper_cfg.label}," said {friend.id}. "That is either clever or completely bananas."'
    )


def perform_rhyme(world: World, hero: Entity, bait_cfg: Bait, rhyme_cfg: RhymeStyle) -> None:
    boar = world.get("boar")
    hero.memes["pluck"] += 1
    hero.meters["acting"] += 1
    boar.memes["listening"] += 1
    if bait_works(BOARS[world.facts["boar_cfg"].id], bait_cfg):
        boar.memes["tempted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} lifted {bait_cfg.phrase} high and called, "
        f'"{rhyme_cfg.chant_a}! {rhyme_cfg.chant_b}!"'
    )
    world.say(
        f"The rhyme was so odd that even the boar seemed to pause and think about it. "
        f"{rhyme_cfg.effect}."
    )


def helper_runs(world: World, friend: Entity, helper_cfg: HelperType, place_cfg: Place) -> None:
    helper = world.get("helper")
    friend.memes["helpfulness"] += 1
    if helper_cfg.delay <= 1:
        helper.meters["ready"] += 1
        world.say(
            f"Meanwhile, {friend.id} dashed down {place_cfg.path} and found {helper_cfg.label}, "
            f"who came at once with {helper_cfg.tool}."
        )
    else:
        world.say(
            f"Meanwhile, {friend.id} dashed down {place_cfg.path} to find {helper_cfg.label}, "
            f"but {helper_cfg.label} was farther off than anyone hoped."
        )
    propagate(world, narrate=False)


def tidy_end(world: World, hero: Entity, friend: Entity, helper_cfg: HelperType, place_cfg: Place, bait_cfg: Bait) -> None:
    helper = world.get("helper")
    helper.meters["ready"] += 1
    boar = world.get("boar")
    boar.memes["tempted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Snout twitching at the smell of {bait_cfg.scent}, the boar followed {hero.id} in a muddy zigzag all the way to {place_cfg.pen}."
    )
    world.say(
        f"There {helper_cfg.label} {helper_cfg.close_method}, and the boar blinked as if it had simply arrived at breakfast by mistake."
    )
    world.say(
        f"For one second the square was silent. Then everybody laughed so hard that even {friend.id} had to lean on the crate."
    )
    world.say(
        f'"That was real pluck," said {helper_cfg.label}. "{hero.id} used a bright distraction instead of a foolish dash."'
    )
    world.say(
        f"After that, the rhyme show began again, and whenever {hero.id} reached the clapping part, the crowd snorted on purpose and clapped twice as loud."
    )


def messy_end(world: World, hero: Entity, friend: Entity, helper_cfg: HelperType, place_cfg: Place, bait_cfg: Bait) -> None:
    boar = world.get("boar")
    boar.meters["mess"] += 1
    world.say(
        f"The boar did follow the smell of {bait_cfg.scent}, but only halfway. Then it swerved past a table, stole a bun, and sent flour puffing into the air like a tiny white cloud."
    )
    world.say(
        f"At last {helper_cfg.label} arrived and {helper_cfg.close_method}, guiding the boar into {place_cfg.pen} before anything worse happened."
    )
    world.say(
        f"No one was hurt, but {friend.id} had flour on the bell, {hero.id} had a cabbage leaf on {hero.pronoun('possessive')} shoulder, and three grandmothers were laughing too hard to speak."
    )
    world.say(
        f'"Next time," {hero.id} said, still giggling, "I will rhyme first and wave second." {friend.id} nodded. Brave pluck had helped, but good timing mattered too.'
    )
    world.say(
        f"Even with the mess, the show went on, and the crowd cheered because {hero.id} had tried to help instead of freezing."
    )


def tell(place_cfg: Place, boar_cfg: BoarType, bait_cfg: Bait, helper_cfg: HelperType, rhyme_cfg: RhymeStyle,
         hero_name: str = "Mina", hero_gender: str = "girl",
         friend_name: str = "Toby", friend_gender: str = "boy",
         trait: str = "bold") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait], label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", label=friend_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, role="helper", label=helper_cfg.label))
    boar = world.add(Entity(id="boar", kind="thing", type="boar", role="boar", label=boar_cfg.label))
    crowd = world.add(Entity(id="crowd", kind="group", type="crowd", role="crowd", label="the crowd"))

    world.facts["boar_cfg"] = boar_cfg
    setup_scene(world, place_cfg, hero, friend, crowd)

    world.para()
    boar_enters(world, boar_cfg, crowd)
    worry(world, hero, friend, place_cfg)

    world.para()
    choose_plan(world, hero, friend, bait_cfg, helper_cfg, rhyme_cfg)
    perform_rhyme(world, hero, bait_cfg, rhyme_cfg)
    helper_runs(world, friend, helper_cfg, place_cfg)

    world.para()
    outcome = "tidy" if outcome_of(
        StoryParams(
            place=place_cfg.id,
            boar=boar_cfg.id,
            bait=bait_cfg.id,
            helper=helper_cfg.id,
            rhyme=rhyme_cfg.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            trait=trait,
            seed=None,
        )
    ) == "tidy" else "messy"
    if outcome == "tidy":
        tidy_end(world, hero, friend, helper_cfg, place_cfg, bait_cfg)
    else:
        messy_end(world, hero, friend, helper_cfg, place_cfg, bait_cfg)

    world.facts.update(
        place=place_cfg,
        boar=boar,
        helper=helper,
        crowd=crowd,
        hero=hero,
        friend=friend,
        bait_cfg=bait_cfg,
        helper_cfg=helper_cfg,
        rhyme_cfg=rhyme_cfg,
        outcome=outcome,
        moral="Brave pluck works best when courage and thoughtfulness work together.",
    )
    return world


PLACES = {
    "fair": Place(
        id="fair",
        label="the village fair",
        crowd="bright bunting fluttered over pie tables",
        treat="hot apple cakes",
        path="the line of jam stalls",
        pen="the orchard gate",
        tags={"fair", "market"},
    ),
    "green": Place(
        id="green",
        label="the town green",
        crowd="a ring of neighbors had set out baskets and stools",
        treat="buttered buns",
        path="the path by the flower cart",
        pen="the little paddock gate",
        tags={"green", "market"},
    ),
    "harvest": Place(
        id="harvest",
        label="the harvest square",
        crowd="striped tents flapped above squash and carrots",
        treat="pear tarts",
        path="the row of pumpkin barrels",
        pen="the cart-yard gate",
        tags={"harvest", "market"},
    ),
}

BOARS = {
    "hungry": BoarType(
        id="hungry",
        label="hungry boar",
        entry="a fence board wobbled, then popped loose",
        muddy="with two leaves stuck to its ear",
        appetite={"fruit", "root"},
        speed=1,
        tags={"boar", "food"},
    ),
    "sniffy": BoarType(
        id="sniffy",
        label="sniffy boar",
        entry="something snorted behind the cider barrels",
        muddy="wearing a necklace of straw like it had dressed for the occasion",
        appetite={"fruit", "sweet"},
        speed=2,
        tags={"boar", "snout"},
    ),
    "grumpy": BoarType(
        id="grumpy",
        label="grumpy boar",
        entry="the turnip cart gave a bump and a low huff came from underneath",
        muddy="with a frown so serious it looked borrowed from a schoolmaster",
        appetite={"root"},
        speed=2,
        tags={"boar", "turnip"},
    ),
}

BAITS = {
    "apples": Bait(
        id="apples",
        label="apples",
        phrase="a shiny string bag of apples",
        scent="apples",
        kind="fruit",
        silly="round and bouncing like red marbles with manners",
        safe=True,
        tags={"apples", "fruit"},
    ),
    "turnips": Bait(
        id="turnips",
        label="turnips",
        phrase="a basket of turnips",
        scent="turnips",
        kind="root",
        silly="lumpy and noble as purple teapots",
        safe=True,
        tags={"turnips", "vegetable"},
    ),
    "bun": Bait(
        id="bun",
        label="honey bun",
        phrase="one sticky honey bun on a napkin",
        scent="honey",
        kind="sweet",
        silly="so glossy it looked ready to slide away on its own",
        safe=True,
        tags={"bun", "sweet"},
    ),
    "marbles": Bait(
        id="marbles",
        label="marbles",
        phrase="a pocketful of marbles",
        scent="nothing at all",
        kind="toy",
        silly="bright but useless for a hungry nose",
        safe=False,
        tags={"marbles", "toy"},
    ),
}

HELPERS = {
    "gardener": HelperType(
        id="gardener",
        label="Mr. Reed the gardener",
        type="gardener",
        tool="a rake held flat like a long wooden arm",
        close_method="swung the gate shut with one neat pull",
        delay=1,
        tags={"gardener", "gate"},
    ),
    "baker": HelperType(
        id="baker",
        label="Mrs. Plum the baker",
        type="woman",
        tool="a flour scoop and a brave apron",
        close_method="clapped a tray and shooed the boar through the gate",
        delay=2,
        tags={"baker", "gate"},
    ),
    "farmer": HelperType(
        id="farmer",
        label="Old Nan the farmer",
        type="woman",
        tool="a long stick and a calm voice",
        close_method="clicked her tongue and closed the gate behind the puzzled boar",
        delay=1,
        tags={"farmer", "gate"},
    ),
}

RHYMES = {
    "bouncy": RhymeStyle(
        id="bouncy",
        opening="Boar with a snore, do not raid the store",
        chant_a="Boar, boar, sniff this more",
        chant_b="march to the gate and not to the tart door",
        effect="The words bounced like balls, and the children in the crowd began clapping before they meant to",
        tags={"rhyme"},
    ),
    "clappy": RhymeStyle(
        id="clappy",
        opening="Snout so stout, turn yourself about",
        chant_a="Snout so stout, hear us shout",
        chant_b="follow the snack and wobble on out",
        effect="The rhyme came out in a cheerful clatter that sounded almost like drumbeats",
        tags={"rhyme"},
    ),
    "marching": RhymeStyle(
        id="marching",
        opening="Boar at the fair, mind your muddy hair",
        chant_a="Boar at the fair, over there",
        chant_b="step to the gate for a root to share",
        effect="The rhyme had such a marching swing that even the geese near the pond honked in time",
        tags={"rhyme"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Ada", "Tess", "Ruby", "Mabel"]
BOY_NAMES = ["Toby", "Finn", "Owen", "Jude", "Milo", "Ben", "Ned", "Arlo"]
TRAITS = ["bold", "steady", "brisk", "careful", "cheerful", "timid"]


@dataclass
class StoryParams:
    place: str
    boar: str
    bait: str
    helper: str
    rhyme: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="fair",
        boar="hungry",
        bait="apples",
        helper="gardener",
        rhyme="bouncy",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Toby",
        friend_gender="boy",
        trait="bold",
        seed=None,
    ),
    StoryParams(
        place="green",
        boar="grumpy",
        bait="turnips",
        helper="farmer",
        rhyme="marching",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        trait="steady",
        seed=None,
    ),
    StoryParams(
        place="harvest",
        boar="sniffy",
        bait="bun",
        helper="baker",
        rhyme="clappy",
        hero_name="Owen",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        place="fair",
        boar="sniffy",
        bait="apples",
        helper="gardener",
        rhyme="bouncy",
        hero_name="Lila",
        hero_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        trait="brisk",
        seed=None,
    ),
]


KNOWLEDGE = {
    "boar": [(
        "What is a boar?",
        "A boar is a wild pig with a strong body and a long snout. It uses its nose to sniff for food."
    )],
    "distraction": [(
        "What is a distraction?",
        "A distraction is something that pulls attention away from one thing and toward another. A smart distraction can help guide a problem away from danger."
    )],
    "pluck": [(
        "What does pluck mean?",
        "Pluck means brave spirit. It is the kind of courage that helps you act even when you feel shaky."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme uses words that sound alike, like 'boar' and 'more.' Rhymes are easy to remember and can sound funny or musical."
    )],
    "gate": [(
        "Why is a gate useful with animals?",
        "A gate can guide an animal into a safe place and keep it from wandering where people are busy. It helps everyone settle down without a chase."
    )],
    "apples": [(
        "Why might an animal follow apples?",
        "Many animals have strong noses and will follow a smell they like. Sweet fruit can pull them in one direction."
    )],
    "turnips": [(
        "Why would turnips work as bait?",
        "Turnips are roots with a strong earthy smell. An animal that likes roots may follow them."
    )],
    "sweet": [(
        "Why can a sweet bun be tempting?",
        "Sweet food has a strong smell and taste. A hungry animal may notice it quickly."
    )],
    "moral": [(
        "What is the moral of this kind of story?",
        "The moral is that bravery works best with thoughtfulness. A calm plan can help more than a wild rush."
    )],
}
KNOWLEDGE_ORDER = ["boar", "distraction", "pluck", "rhyme", "gate", "apples", "turnips", "sweet", "moral"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    boar_cfg = f["boar_cfg"]
    bait_cfg = f["bait_cfg"]
    rhyme_cfg = f["rhyme_cfg"]
    place = f["place"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "distraction," "pluck," and "boar," and ends with a gentle moral.',
        f"Tell a comedy set at {place.label} where {hero.id} uses a silly rhyme and {bait_cfg.label} to distract a {boar_cfg.label}.",
        f'Write a child-facing story with a rhyme like "{rhyme_cfg.chant_a}" and show that brave pluck works best with a smart plan.',
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    boar_cfg = f["boar_cfg"]
    bait_cfg = f["bait_cfg"]
    helper_cfg = f["helper_cfg"]
    outcome = f["outcome"]
    moral = f["moral"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id} at {place.label}, plus a muddy {boar_cfg.label} that blundered into the crowd."
        ),
        (
            "What problem started the story?",
            f"The trouble started when the boar wandered into the busy gathering and everyone lost track of the show. The crowd worried the boar would charge toward the food tables and make a giant mess."
        ),
        (
            f"How did {hero.id} try to help?",
            f"{hero.id} used pluck to step forward with {bait_cfg.phrase} and a silly rhyme. That distraction gave the boar something safer to follow than the crowded tables."
        ),
        (
            f"Why did the rhyme matter?",
            f"The rhyme helped {hero.id} hold everyone's attention and made the distraction bigger and clearer. It also kept the scene funny instead of turning into a scary chase."
        ),
    ]
    if outcome == "tidy":
        qa.append((
            "How did the story end?",
            f"The boar followed the smell toward the gate, and {helper_cfg.label} shut it safely behind him. After that, the crowd laughed and the rhyme show began again, proving that a calm plan had changed the day."
        ))
    else:
        qa.append((
            "Was everything perfect at the end?",
            f"No, not quite. The boar caused a little mess before {helper_cfg.label} guided it through the gate, but no one was hurt and the children still learned from it."
        ))
    qa.append((
        "What is the moral of the story?",
        f"{moral} {hero.id} was brave, but the story also shows that brave hearts need good timing and good thinking."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"boar", "distraction", "pluck", "rhyme", "gate", "moral"}
    bait_cfg = world.facts["bait_cfg"]
    if bait_cfg.kind == "fruit":
        tags.add("apples")
    elif bait_cfg.kind == "root":
        tags.add("turnips")
    elif bait_cfg.kind == "sweet":
        tags.add("sweet")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(boar_cfg: BoarType, bait_cfg: Bait) -> str:
    if not bait_cfg.safe:
        return (
            f"(No story: {bait_cfg.label} is not a safe distraction for a hungry animal. "
            f"Use food with a real smell, like apples, turnips, or a bun.)"
        )
    return (
        f"(No story: a {boar_cfg.label} would not reasonably follow {bait_cfg.label}. "
        f"Pick bait that matches what this boar would sniff for.)"
    )


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    return (
        f"(Refusing helper '{helper_id}': {helper.label} is too slow for this storyworld's safety gate. "
        f"Choose a helper who can reach the gate quickly.)"
    )


ASP_RULES = r"""
safe_bait(B) :- bait(B), bait_safe(B).
bait_works(Boar, B) :- appetite(Boar, K), bait_kind(B, K), safe_bait(B).
valid(P, Boar, B) :- place(P), boar(Boar), bait(B), bait_works(Boar, B).

rhyme_power(R, 1) :- rhyme(R).
brave(T) :- trait(T), pluck_of(T, P), brave_min(M), P >= M.
control(T, R, P + Q) :- pluck_of(T, P), rhyme_power(R, Q).

tidy :- chosen_trait(T), chosen_rhyme(R), chosen_boar(B), chosen_helper(H),
        control(T, R, C), speed(B, S), helper_delay(H, D), C >= S + D + 1.
messy :- not tidy.

outcome(tidy) :- tidy.
outcome(messy) :- messy.

sensible_helper(H) :- helper(H), helper_delay(H, D), sense_min(M), D <= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for bid, boar in BOARS.items():
        lines.append(asp.fact("boar", bid))
        lines.append(asp.fact("speed", bid, boar.speed))
        for k in sorted(boar.appetite):
            lines.append(asp.fact("appetite", bid, k))
    for bait_id, bait in BAITS.items():
        lines.append(asp.fact("bait", bait_id))
        lines.append(asp.fact("bait_kind", bait_id, bait.kind))
        if bait.safe:
            lines.append(asp.fact("bait_safe", bait_id))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_delay", hid, helper.delay))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme", rid))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("pluck_of", trait, pluck_score(trait)))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("brave_min", PLUCK_BRAVE))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_helpers() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_helper/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible_helper"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_rhyme", params.rhyme),
        asp.fact("chosen_boar", params.boar),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_helpers = set(asp_sensible_helpers())
    python_helpers = {hid for hid, helper in HELPERS.items() if helper_sensible(helper)}
    if clingo_helpers == python_helpers:
        print(f"OK: sensible helpers match ({sorted(clingo_helpers)}).")
    else:
        rc = 1
        print("MISMATCH in sensible helpers:", sorted(clingo_helpers), sorted(python_helpers))

    cases = list(CURATED)
    for s in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(p)
        except StoryError:
            pass
    bad = 0
    for p in cases:
        try:
            if asp_outcome(p) != outcome_of(p):
                bad += 1
        except StoryError:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child uses rhyme, pluck, and a safe distraction to guide a boar away."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--boar", choices=BOARS)
    ap.add_argument("--bait", choices=BAITS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--gender", choices=["girl", "boy"], help="hero gender")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.boar and args.bait:
        boar = BOARS[args.boar]
        bait = BAITS[args.bait]
        if not bait_works(boar, bait):
            raise StoryError(explain_rejection(boar, bait))
    if args.helper and not helper_sensible(HELPERS[args.helper]):
        raise StoryError(explain_helper(args.helper))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.boar is None or c[1] == args.boar)
        and (args.bait is None or c[2] == args.bait)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, boar, bait = rng.choice(sorted(combos))
    helper_choices = sorted(hid for hid, helper in HELPERS.items() if helper_sensible(helper))
    helper = args.helper or rng.choice(helper_choices)
    rhyme = args.rhyme or rng.choice(sorted(RHYMES))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        boar=boar,
        bait=bait,
        helper=helper,
        rhyme=rhyme,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("(Invalid params: unknown place.)")
    if params.boar not in BOARS:
        raise StoryError("(Invalid params: unknown boar.)")
    if params.bait not in BAITS:
        raise StoryError("(Invalid params: unknown bait.)")
    if params.helper not in HELPERS:
        raise StoryError("(Invalid params: unknown helper.)")
    if params.rhyme not in RHYMES:
        raise StoryError("(Invalid params: unknown rhyme.)")
    if params.trait not in TRAITS:
        raise StoryError("(Invalid params: unknown trait.)")
    boar = BOARS[params.boar]
    bait = BAITS[params.bait]
    helper = HELPERS[params.helper]
    if not bait_works(boar, bait):
        raise StoryError(explain_rejection(boar, bait))
    if not helper_sensible(helper):
        raise StoryError(explain_helper(params.helper))

    world = tell(
        place_cfg=PLACES[params.place],
        boar_cfg=boar,
        bait_cfg=bait,
        helper_cfg=helper,
        rhyme_cfg=RHYMES[params.rhyme],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible_helper/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible helpers: {', '.join(asp_sensible_helpers())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, boar, bait) combos:\n")
        for place, boar, bait in combos:
            print(f"  {place:8} {boar:8} {bait}")
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
            header = f"### {p.hero_name}: {p.boar} boar with {p.bait} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
