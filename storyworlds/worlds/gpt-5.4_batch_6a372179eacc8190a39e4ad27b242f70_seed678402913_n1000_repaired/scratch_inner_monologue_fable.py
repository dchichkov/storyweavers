#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scratch_inner_monologue_fable.py
===========================================================

A small story world for a fable-like tale about impatience, bark, and a single
tempting scratch.

The seed asked for:
- the word "scratch"
- inner monologue
- a fable-like style

This world models a hungry little animal who wants fruit from a living plant and
is tempted to scratch the bark or stems to hurry things along. A wiser friend
either talks the hero out of it, or the hero learns after one unkind scratch
that greed hurts the very thing that feeds them. The resolution depends on the
actual plant and on a repair/harvest method that must make common sense.

Run it
------
    python storyworlds/worlds/gpt-5.4/scratch_inner_monologue_fable.py
    python storyworlds/worlds/gpt-5.4/scratch_inner_monologue_fable.py --source berry_bush
    python storyworlds/worlds/gpt-5.4/scratch_inner_monologue_fable.py --source apple_tree --fix stool_reach
    python storyworlds/worlds/gpt-5.4/scratch_inner_monologue_fable.py --source apple_tree --fix basket_pick   # rejected
    python storyworlds/worlds/gpt-5.4/scratch_inner_monologue_fable.py --all
    python storyworlds/worlds/gpt-5.4/scratch_inner_monologue_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/scratch_inner_monologue_fable.py --trace
    python storyworlds/worlds/gpt-5.4/scratch_inner_monologue_fable.py --json
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
# from the nested directory storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HEEDFUL_TRAITS = {"patient", "gentle", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    gender: str = "neutral"
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        table = {
            "female": {"subject": "she", "object": "her", "possessive": "her"},
            "male": {"subject": "he", "object": "him", "possessive": "his"},
            "neutral": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return table.get(self.gender, table["neutral"])[case]


@dataclass
class Setting:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    fruit: str
    fruit_phrase: str
    height: str
    ripe_now: bool
    sturdy: bool
    thorny: bool = False
    bark_word: str = "bark"
    home: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    method: str
    tail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    source: str
    fix: str
    hero_name: str
    hero_type: str
    hero_gender: str
    friend_name: str
    friend_type: str
    friend_gender: str
    trait: str
    hero_age: int = 4
    friend_age: int = 6
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_hurt_source(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    hero = world.entities.get("hero")
    if source is None or hero is None:
        return out
    if source.meters["scratched"] < THRESHOLD:
        return out
    sig = ("hurt_source", "source")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["hurt"] += 1
    hero.memes["shame"] += 1
    if source.attrs.get("ripe_now"):
        source.meters["fruit_ready"] = 1.0
    else:
        source.meters["blossoms_lost"] += 1
    out.append("__hurt__")
    return out


def _r_thorns(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    hero = world.entities.get("hero")
    if source is None or hero is None:
        return out
    if source.meters["scratched"] < THRESHOLD or not source.attrs.get("thorny"):
        return out
    sig = ("thorns", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["paw_sore"] += 1
    hero.memes["regret"] += 1
    out.append("__thorn__")
    return out


def _r_water_ripens(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    if source is None:
        return out
    if source.meters["watered"] < THRESHOLD or source.attrs.get("ripe_now"):
        return out
    sig = ("water_ripens", "source")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["fruit_ready"] = 1.0
    out.append("__ripe__")
    return out


def _r_harvest(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    source = world.entities.get("source")
    if hero is None or source is None:
        return out
    if source.meters["harvested"] < THRESHOLD:
        return out
    sig = ("full_belly", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["hunger"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    out.append("__fed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt_source", tag="physical", apply=_r_hurt_source),
    Rule(name="thorns", tag="physical", apply=_r_thorns),
    Rule(name="water_ripens", tag="physical", apply=_r_water_ripens),
    Rule(name="harvest", tag="physical", apply=_r_harvest),
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
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "orchard": Setting(
        id="orchard",
        label="a sunny orchard path",
        mood="Bees drowsed over clover, and the leaves held little coins of light.",
        affords={"apple_tree", "pear_tree", "plum_tree"},
    ),
    "garden": Setting(
        id="garden",
        label="a cottage garden",
        mood="The air smelled of warm soil, and every bed looked neat except where children of the woods had played.",
        affords={"apple_tree", "pear_tree", "berry_bush"},
    ),
    "brookside": Setting(
        id="brookside",
        label="the green bank beside a brook",
        mood="The brook talked softly to the stones, as if it already knew a lesson and was waiting to see who would learn it.",
        affords={"plum_tree", "berry_bush"},
    ),
}

SOURCES = {
    "apple_tree": Source(
        id="apple_tree",
        label="apple tree",
        fruit="apples",
        fruit_phrase="round red apples",
        height="high",
        ripe_now=False,
        sturdy=True,
        bark_word="bark",
        home="a robin's nest",
        tags={"tree", "apples", "waiting"},
    ),
    "pear_tree": Source(
        id="pear_tree",
        label="pear tree",
        fruit="pears",
        fruit_phrase="golden pears",
        height="medium",
        ripe_now=True,
        sturdy=True,
        bark_word="bark",
        home="a sleepy dove",
        tags={"tree", "pears", "harvest"},
    ),
    "plum_tree": Source(
        id="plum_tree",
        label="plum tree",
        fruit="plums",
        fruit_phrase="dark purple plums",
        height="high",
        ripe_now=True,
        sturdy=True,
        bark_word="bark",
        home="a little finch",
        tags={"tree", "plums", "harvest"},
    ),
    "berry_bush": Source(
        id="berry_bush",
        label="berry bush",
        fruit="berries",
        fruit_phrase="bright red berries",
        height="low",
        ripe_now=True,
        sturdy=False,
        thorny=True,
        bark_word="stems",
        home="a tiny wren",
        tags={"bush", "berries", "thorns"},
    ),
}

FIXES = {
    "basket_pick": Fix(
        id="basket_pick",
        label="a little basket",
        method="brought a little basket and picked only the fruit that was easy to reach",
        tail="Soon the basket was dotted with careful little treasures.",
        tags={"basket", "gentle_hands"},
    ),
    "stool_reach": Fix(
        id="stool_reach",
        label="a low wooden stool",
        method="set a low wooden stool beneath the branches and reached up slowly",
        tail="From the stool, the fruit could be taken one by one without hurting anything that lived.",
        tags={"stool", "careful_reach"},
    ),
    "sheet_catch": Fix(
        id="sheet_catch",
        label="a clean old sheet",
        method="spread a clean old sheet below the tree and gave the branch the gentlest shake",
        tail="The ripe fruit dropped with soft little taps, and not one was bruised.",
        tags={"sheet", "gentle_shake"},
    ),
    "wait_water": Fix(
        id="wait_water",
        label="a small watering can",
        method="carried a small watering can to the roots and chose patience over clawing",
        tail="By the next bright morning, the fruit had ripened enough to be gathered gladly.",
        tags={"water", "patience"},
    ),
}

NAMES = {
    "squirrel": ["Pip", "Nim", "Tavi"],
    "rabbit": ["Moss", "Poppy", "Fern"],
    "fox": ["Rill", "Bram", "Sable"],
    "mouse": ["Tansy", "Pico", "Lark"],
    "tortoise": ["Clover", "Milo", "Thyme"],
    "hedgehog": ["Hazel", "Pebble", "Burr"],
}

ANIMAL_GENDERS = ["female", "male", "neutral"]
ANIMAL_TYPES = sorted(NAMES)
TRAITS = ["patient", "thoughtful", "gentle", "eager", "proud", "restless"]


def compatible_fix(source: Source, fix: Fix) -> bool:
    if fix.id == "basket_pick":
        return source.height == "low" and source.ripe_now
    if fix.id == "stool_reach":
        return source.ripe_now and source.height in {"medium", "high"} and source.sturdy
    if fix.id == "sheet_catch":
        return source.ripe_now and source.height in {"medium", "high"} and source.sturdy
    if fix.id == "wait_water":
        return not source.ripe_now
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for source_id in sorted(setting.affords):
            source = SOURCES[source_id]
            for fix_id, fix in FIXES.items():
                if compatible_fix(source, fix):
                    combos.append((setting_id, source_id, fix_id))
    return sorted(combos)


def would_avert(trait: str, hero_age: int, friend_age: int) -> bool:
    return trait in HEEDFUL_TRAITS and friend_age > hero_age


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.trait, params.hero_age, params.friend_age) else "mended"


def explain_rejection(source: Source, fix: Fix) -> str:
    if fix.id == "basket_pick":
        return (
            f"(No story: {fix.label} only makes sense for low, ripe fruit, but the "
            f"{source.label} keeps its {source.fruit} too far from the ground for basket-picking.)"
        )
    if fix.id == "stool_reach":
        return (
            f"(No story: {fix.label} helps with ripe fruit you can reach carefully, "
            f"but the {source.label} is not a good stool story here.)"
        )
    if fix.id == "sheet_catch":
        return (
            f"(No story: a sheet is for catching ripe fruit from a sturdy tree, "
            f"not for the {source.label}.)"
        )
    if fix.id == "wait_water":
        return (
            f"(No story: waiting with water makes sense when fruit still needs time, "
            f"but the {source.label} already has ripe {source.fruit}.)"
        )
    return "(No story: that repair does not fit this plant.)"


def predict_scratch(world: World) -> dict:
    sim = world.copy()
    source = sim.get("source")
    source.meters["scratched"] += 1
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    return {
        "hurt": source.meters["hurt"] >= THRESHOLD,
        "paw_sore": hero.meters["paw_sore"] >= THRESHOLD,
        "blossoms_lost": source.meters["blossoms_lost"] >= THRESHOLD,
    }


def scene_open(world: World, hero: Entity, friend: Entity, source: Source) -> None:
    world.say(
        f"In {world.setting.label}, {hero.id} the {hero.type} and {friend.id} the "
        f"{friend.type} came upon a {source.label} full of {source.fruit_phrase}."
    )
    world.say(world.setting.mood)
    world.say(
        f"{hero.id}'s stomach gave a small empty rumble, and the sight of the {source.fruit} "
        f"made {hero.pronoun('possessive')} eyes shine."
    )


def temptation(world: World, hero: Entity, source: Source) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f'"If I give the {source.bark_word} just one quick scratch," {hero.id} thought, '
        f'"surely the {source.fruit} will tumble down faster than waiting."'
    )


def warning(world: World, hero: Entity, friend: Entity, source: Source) -> None:
    pred = predict_scratch(world)
    world.facts["predicted_hurt"] = pred["hurt"]
    world.facts["predicted_paw"] = pred["paw_sore"]
    caution = f'"Do not be hasty," said {friend.id}. "The {source.label} is feeding us, not fighting us."'
    if pred["blossoms_lost"]:
        caution += f' "{source.fruit_phrase.capitalize()} do not come from claw marks. They come from time."'
    elif pred["paw_sore"]:
        caution += f' "{source.label.capitalize()} has thorns, and a greedy paw is soon a sore one."'
    else:
        caution += f' "A hungry claw can wound the very branch that offers supper."'
    world.say(caution)


def back_down(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["wisdom"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f'{hero.id} drew back {hero.pronoun("possessive")} paw at once. '
        f'"A fast claw is not a wise claw," {hero.pronoun()} thought.'
    )
    world.say(
        f"{friend.id} smiled, for good advice is sweetest when it arrives before harm."
    )


def scratch(world: World, hero: Entity, source_ent: Entity, source: Source) -> None:
    source_ent.meters["scratched"] += 1
    propagate(world, narrate=False)
    hero.memes["defiance"] += 1
    base = (
        f"But hunger spoke louder than patience. {hero.id} reached out and gave the "
        f"{source.bark_word} a sharp scratch."
    )
    if source_ent.meters["hurt"] >= THRESHOLD:
        base += f" The {source.label} seemed to flinch, and even {source.home or 'the leaves'} stirred unhappily."
    world.say(base)
    if hero.meters["paw_sore"] >= THRESHOLD:
        world.say(
            f"A thorn pricked {hero.pronoun('possessive')} paw, and {hero.id} snatched it back with a little gasp."
        )
    if source_ent.meters["blossoms_lost"] >= THRESHOLD:
        world.say(
            "A few pale blossoms drifted down before their time, and there was no fruit to show for the damage."
        )


def remorse(world: World, hero: Entity, source: Source) -> None:
    thoughts = []
    if hero.meters["paw_sore"] >= THRESHOLD:
        thoughts.append("a sore paw")
    if world.get("source").meters["blossoms_lost"] >= THRESHOLD:
        thoughts.append("fallen blossoms")
    if not thoughts:
        thoughts.append(f"the hurt look of the {source.label}")
    joined = " and ".join(thoughts)
    world.say(
        f'"What a foolish bargain," {hero.id} thought. "I traded kindness for {joined}."'
    )


def use_fix(world: World, hero: Entity, friend: Entity, source_ent: Entity, source: Source, fix: Fix) -> None:
    hero.memes["gratitude"] += 1
    hero.memes["wisdom"] += 1
    if fix.id == "basket_pick":
        source_ent.meters["fruit_ready"] = 1.0
        source_ent.meters["harvested"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{friend.id} said nothing sharp in return. Instead, the two friends {fix.method}.'
        )
        world.say(fix.tail)
    elif fix.id == "stool_reach":
        source_ent.meters["fruit_ready"] = 1.0
        source_ent.meters["harvested"] += 1
        propagate(world, narrate=False)
        world.say(
            f'"Let us do this the honest way," said {friend.id}, and they {fix.method}.'
        )
        world.say(fix.tail)
    elif fix.id == "sheet_catch":
        source_ent.meters["fruit_ready"] = 1.0
        source_ent.meters["harvested"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{friend.id} fetched {fix.label}, and together they {fix.method}.'
        )
        world.say(fix.tail)
    elif fix.id == "wait_water":
        source_ent.meters["watered"] += 1
        propagate(world, narrate=False)
        source_ent.meters["harvested"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{hero.id} bowed {hero.pronoun("possessive")} head. Then the two friends {fix.method}.'
        )
        world.say(
            "They went home with empty paws that evening, but they had not gone home empty-hearted."
        )
        world.say(fix.tail)


def closing(world: World, hero: Entity, friend: Entity, source: Source, outcome: str) -> None:
    if outcome == "averted":
        world.say(
            f"Before sunset, {hero.id} and {friend.id} had enough {source.fruit} for both of them, "
            f"and the {source.label} stood unharmed in the gold light."
        )
    else:
        if world.get("source").meters["harvested"] >= THRESHOLD:
            world.say(
                f"When they ate, {hero.id} found the {source.fruit} sweeter for having been earned gently."
            )
    world.say(
        f"And so it was remembered in that place: one greedy scratch may be quick, "
        f"but patience feeds both paw and root."
    )


def tell(
    setting: Setting,
    source: Source,
    fix: Fix,
    hero_name: str,
    hero_type: str,
    hero_gender: str,
    friend_name: str,
    friend_type: str,
    friend_gender: str,
    trait: str,
    hero_age: int,
    friend_age: int,
) -> World:
    world = World(setting=setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            label=f"{hero_name} the {hero_type}",
            gender=hero_gender,
            role="hero",
            traits=[trait],
            attrs={"age": hero_age},
            tags={"animal"},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_type,
            label=f"{friend_name} the {friend_type}",
            gender=friend_gender,
            role="friend",
            traits=["wise"],
            attrs={"age": friend_age},
            tags={"animal"},
        )
    )
    source_ent = world.add(
        Entity(
            id="source",
            kind="thing",
            type="plant",
            label=source.label,
            phrase=source.fruit_phrase,
            attrs={
                "ripe_now": source.ripe_now,
                "height": source.height,
                "thorny": source.thorny,
                "sturdy": source.sturdy,
                "home": source.home,
                "fruit": source.fruit,
            },
            tags=set(source.tags),
        )
    )
    hero.meters["hunger"] = 1.0

    scene_open(world, hero, friend, source)
    world.para()
    temptation(world, hero, source)
    warning(world, hero, friend, source)

    averted = would_avert(trait, hero_age, friend_age)
    if averted:
        back_down(world, hero, friend)
        world.para()
        use_fix(world, hero, friend, source_ent, source, fix)
    else:
        world.para()
        scratch(world, hero, source_ent, source)
        remorse(world, hero, source)
        world.para()
        use_fix(world, hero, friend, source_ent, source, fix)

    world.para()
    outcome = "averted" if averted else "mended"
    closing(world, hero, friend, source, outcome)
    world.facts.update(
        hero=hero,
        friend=friend,
        source_cfg=source,
        source=source_ent,
        fix=fix,
        outcome=outcome,
        averted=averted,
        scratched=source_ent.meters["scratched"] >= THRESHOLD,
        paw_sore=hero.meters["paw_sore"] >= THRESHOLD,
        blossoms_lost=source_ent.meters["blossoms_lost"] >= THRESHOLD,
        harvested=source_ent.meters["harvested"] >= THRESHOLD,
        setting=setting,
    )
    return world


KNOWLEDGE = {
    "tree": [
        (
            "Why should you be gentle with a tree?",
            "A tree is alive, and its bark protects what is growing inside. Hurting the bark can hurt the tree."
        )
    ],
    "bush": [
        (
            "Why can a berry bush be tricky to pick from?",
            "Berry bushes can have thorns, and thorns can prick your paws or fingers. That is why careful picking matters."
        )
    ],
    "waiting": [
        (
            "Why do some fruit need more time before you pick it?",
            "Fruit ripens slowly. Time, sun, and water help it grow sweet enough to eat."
        )
    ],
    "basket": [
        (
            "What is a basket good for when picking fruit?",
            "A basket holds fruit gently, so it does not get squashed. It also helps you take only what you can carry carefully."
        )
    ],
    "stool": [
        (
            "Why is a stool better than clawing at a branch?",
            "A stool helps you reach higher in a steady way. Clawing or scratching can hurt the plant and still not get the fruit safely."
        )
    ],
    "sheet": [
        (
            "Why might someone put a sheet under a fruit tree?",
            "A sheet can catch ripe fruit softly if it drops. That keeps the fruit cleaner and helps stop it from getting bruised."
        )
    ],
    "water": [
        (
            "How does watering help a plant?",
            "Water helps a plant stay healthy and keep growing. A cared-for plant can make better fruit."
        )
    ],
    "gentle_hands": [
        (
            "Why are gentle hands important when picking fruit?",
            "Gentle hands take only what is ready and do not tear branches or stems. Kindness helps the plant keep giving."
        )
    ],
}
KNOWLEDGE_ORDER = ["tree", "bush", "waiting", "basket", "stool", "sheet", "water", "gentle_hands"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    source = world.facts["source_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "averted":
        return [
            f'Write a short fable for a young child that includes the word "scratch" and uses inner monologue. '
            f'The hero is {hero.id} the {hero.type}, who almost hurts a {source.label} out of impatience but listens to wiser advice.',
            f"Tell a woodland fable where {hero.id} thinks about giving a plant a quick scratch to hurry down some {source.fruit}, "
            f"then chooses patience instead and is rewarded.",
            f'Write a gentle moral tale with a talking-thought line like "If I give it one quick scratch..." and end by showing '
            f"that kindness to living things brings a better supper.",
        ]
    return [
        f'Write a short fable for a young child that includes the word "scratch" and uses inner monologue. '
        f'The hero is {hero.id} the {hero.type}, who learns that a greedy claw can hurt the very thing that feeds {hero.pronoun("object")}.',
        f"Tell a woodland moral tale where a hungry little animal gives a {source.label} a scratch, regrets it, and then learns a gentler way to gather {source.fruit}.",
        f'Write a simple fable with one mistaken act, one reflective thought, and an ending image that proves patience is wiser than haste.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    source = world.facts["source_cfg"]
    fix = world.facts["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, who wanted {source.fruit}, and {friend.id} the {friend.type}, who tried to guide {hero.pronoun('object')} wisely."
        ),
        (
            f"What did {hero.id} want from the {source.label}?",
            f"{hero.id} wanted the {source.fruit} because {hero.pronoun()} was hungry. The sight of the fruit made {hero.pronoun('possessive')} impatience grow."
        ),
        (
            "What was the tempting idea in the hero's thoughts?",
            f"{hero.id} thought that one quick scratch on the {source.bark_word} might make the {source.fruit} fall faster. That inner thought shows how haste can sound clever before it is tested."
        ),
    ]
    if world.facts["averted"]:
        qa.append(
            (
                f"Why did {hero.id} stop before scratching the {source.label}?",
                f"{friend.id} warned that hurting the plant would be foolish, and {hero.id} listened. Because {friend.id} was older and {hero.id} was in a heedful mood, the warning changed the choice before harm was done."
            )
        )
    else:
        hurt_parts = []
        if world.facts["paw_sore"]:
            hurt_parts.append(f"{hero.id}'s paw was pricked")
        if world.facts["blossoms_lost"]:
            hurt_parts.append("blossoms fell before their time")
        if not hurt_parts:
            hurt_parts.append(f"the {source.label} was hurt")
        qa.append(
            (
                f"What happened after {hero.id} gave the {source.label} a scratch?",
                f"{'; '.join(hurt_parts).capitalize()}. That is when {hero.id} understood that a quick claw can cause trouble instead of bringing supper."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They used {fix.label}, and they {fix.method}. The new method worked because it matched the kind of plant and treated it gently."
        )
    )
    qa.append(
        (
            "What is the lesson of the story?",
            f"The lesson is that impatience can harm the very thing you need. Patience and gentle care brought the fruit, but a greedy scratch did not."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["source_cfg"].tags) | set(world.facts["fix"].tags)
    if "tree" in tags or "apples" in tags or "pears" in tags or "plums" in tags:
        tags.add("tree")
    if "bush" in tags or "berries" in tags or "thorns" in tags:
        tags.add("bush")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        source="berry_bush",
        fix="basket_pick",
        hero_name="Pip",
        hero_type="squirrel",
        hero_gender="neutral",
        friend_name="Clover",
        friend_type="tortoise",
        friend_gender="female",
        trait="restless",
        hero_age=4,
        friend_age=7,
    ),
    StoryParams(
        setting="orchard",
        source="apple_tree",
        fix="wait_water",
        hero_name="Moss",
        hero_type="rabbit",
        hero_gender="male",
        friend_name="Hazel",
        friend_type="hedgehog",
        friend_gender="female",
        trait="patient",
        hero_age=4,
        friend_age=6,
    ),
    StoryParams(
        setting="orchard",
        source="pear_tree",
        fix="stool_reach",
        hero_name="Tansy",
        hero_type="mouse",
        hero_gender="female",
        friend_name="Bram",
        friend_type="fox",
        friend_gender="male",
        trait="proud",
        hero_age=5,
        friend_age=5,
    ),
    StoryParams(
        setting="brookside",
        source="plum_tree",
        fix="sheet_catch",
        hero_name="Fern",
        hero_type="rabbit",
        hero_gender="female",
        friend_name="Milo",
        friend_type="tortoise",
        friend_gender="male",
        trait="thoughtful",
        hero_age=3,
        friend_age=7,
    ),
]


ASP_RULES = r"""
mid_or_high(S) :- height(S, medium).
mid_or_high(S) :- height(S, high).

compatible(S, basket_pick) :- ripe_now(S), height(S, low).
compatible(S, stool_reach) :- ripe_now(S), sturdy(S), mid_or_high(S).
compatible(S, sheet_catch) :- ripe_now(S), sturdy(S), mid_or_high(S).
compatible(S, wait_water)  :- not ripe_now(S).

valid(Place, S, F) :- affords(Place, S), compatible(S, F).

averted :- trait(T), heedful(T), friend_age(FA), hero_age(HA), FA > HA.
outcome(averted) :- averted.
outcome(mended)  :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for source_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("height", source_id, source.height))
        if source.ripe_now:
            lines.append(asp.fact("ripe_now", source_id))
        if source.sturdy:
            lines.append(asp.fact("sturdy", source_id))
    for fix_id in FIXES:
        lines.append(asp.fact("fix", fix_id))
    for trait in sorted(HEEDFUL_TRAITS):
        lines.append(asp.fact("heedful", trait))
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
            asp.fact("trait", params.trait),
            asp.fact("hero_age", params.hero_age),
            asp.fact("friend_age", params.friend_age),
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
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fable about one scratch, one thought, and a wiser way."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-type", choices=ANIMAL_TYPES)
    ap.add_argument("--friend-type", choices=ANIMAL_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, animal_type: str, avoid: str = "") -> str:
    pool = [n for n in NAMES[animal_type] if n != avoid]
    if not pool:
        pool = list(NAMES[animal_type])
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.source and args.source not in SETTINGS[args.setting].affords:
        raise StoryError(
            f"(No story: {SOURCES[args.source].label} does not belong in {SETTINGS[args.setting].label} here.)"
        )
    if args.source and args.fix:
        source = SOURCES[args.source]
        fix = FIXES[args.fix]
        if not compatible_fix(source, fix):
            raise StoryError(explain_rejection(source, fix))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.source is None or c[1] == args.source)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, source_id, fix_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(ANIMAL_TYPES)
    friend_type = args.friend_type or rng.choice(ANIMAL_TYPES)
    hero_name = pick_name(rng, hero_type)
    friend_name = pick_name(rng, friend_type, avoid=hero_name)
    hero_gender = rng.choice(ANIMAL_GENDERS)
    friend_gender = rng.choice(ANIMAL_GENDERS)
    trait = args.trait or rng.choice(TRAITS)
    hero_age = rng.randint(3, 6)
    friend_age = rng.randint(4, 8)
    return StoryParams(
        setting=setting_id,
        source=source_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_type=hero_type,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_type=friend_type,
        friend_gender=friend_gender,
        trait=trait,
        hero_age=hero_age,
        friend_age=friend_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    setting = SETTINGS[params.setting]
    source = SOURCES[params.source]
    fix = FIXES[params.fix]
    if params.source not in setting.affords:
        raise StoryError(
            f"(No story: {source.label} does not belong in {setting.label} here.)"
        )
    if not compatible_fix(source, fix):
        raise StoryError(explain_rejection(source, fix))

    world = tell(
        setting=setting,
        source=source,
        fix=fix,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        friend_gender=params.friend_gender,
        trait=params.trait,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
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
        print(f"{len(combos)} compatible (setting, source, fix) combos:\n")
        for setting_id, source_id, fix_id in combos:
            print(f"  {setting_id:10} {source_id:11} {fix_id}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.source} with {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
