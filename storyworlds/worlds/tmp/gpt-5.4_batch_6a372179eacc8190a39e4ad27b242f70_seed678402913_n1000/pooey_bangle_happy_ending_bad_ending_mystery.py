#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pooey_bangle_happy_ending_bad_ending_mystery.py
============================================================================

A tiny mystery storyworld about a missing bangle, a pooey smell, and a search
that can end happily or sadly.

The world model is deliberately small and classical:
- a child wears a beloved bangle
- a sudden pooey smell makes the child jerk away
- the bangle slips loose and rolls into a plausible hiding place
- a helper searches by either following clues or making a weak guess
- if the method is good enough for the hiding place, the mystery is solved
- if not, the bangle is lost for now, and the ending stays sad

Run it
------
python storyworlds/worlds/gpt-5.4/pooey_bangle_happy_ending_bad_ending_mystery.py
python storyworlds/worlds/gpt-5.4/pooey_bangle_happy_ending_bad_ending_mystery.py --place porch --source compost_pail --spot drain_grate
python storyworlds/worlds/gpt-5.4/pooey_bangle_happy_ending_bad_ending_mystery.py --method guess --delay 2
python storyworlds/worlds/gpt-5.4/pooey_bangle_happy_ending_bad_ending_mystery.py --all
python storyworlds/worlds/gpt-5.4/pooey_bangle_happy_ending_bad_ending_mystery.py --qa --json
python storyworlds/worlds/gpt-5.4/pooey_bangle_happy_ending_bad_ending_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    line: str
    sources: set[str] = field(default_factory=set)
    spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SmellSource:
    id: str
    label: str
    phrase: str
    line: str
    clue: str
    startle: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    clue: str
    retrieve: str
    fail: str
    difficulty: int = 1
    lost_after_delay: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SearchMethod:
    id: str
    label: str
    line: str
    success: str
    failure: str
    power: int = 1
    sense: int = 1
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


def _r_lost_mystery(world: World) -> list[str]:
    bangle = world.entities.get("bangle")
    hero = world.entities.get("hero")
    if not bangle or not hero:
        return []
    if bangle.meters["hidden"] < THRESHOLD:
        return []
    sig = ("mystery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_drain_loss(world: World) -> list[str]:
    bangle = world.entities.get("bangle")
    if not bangle:
        return []
    if bangle.attrs.get("spot") != "drain_grate":
        return []
    if bangle.meters["delay"] < THRESHOLD:
        return []
    sig = ("drain_loss",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bangle.meters["far_away"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="lost_mystery", tag="emotional", apply=_r_lost_mystery),
    Rule(name="drain_loss", tag="physical", apply=_r_drain_loss),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the back porch",
        line="The back porch was dim and rainy, with little shadows under every board.",
        sources={"compost_pail", "muddy_boot"},
        spots={"doormat", "drain_grate"},
        tags={"porch"},
    ),
    "hallway": Place(
        id="hallway",
        label="hallway",
        phrase="the front hallway",
        line="The front hallway held coat hooks, quiet corners, and a long strip of rug like a secret path.",
        sources={"old_lunchbox", "muddy_boot"},
        spots={"toy_chest", "doormat"},
        tags={"hallway"},
    ),
    "garden_shed": Place(
        id="garden_shed",
        label="shed",
        phrase="the garden shed",
        line="The garden shed felt full of wooden creaks and dusty little mysteries.",
        sources={"compost_pail", "old_lunchbox"},
        spots={"flowerpot", "toy_chest"},
        tags={"shed"},
    ),
}

SOURCES = {
    "compost_pail": SmellSource(
        id="compost_pail",
        label="compost pail",
        phrase="the compost pail",
        line='A sudden pooey smell puffed out from the compost pail by the door.',
        clue="a wet leaf stuck to the floor nearby",
        startle=1,
        tags={"pooey", "compost"},
    ),
    "muddy_boot": SmellSource(
        id="muddy_boot",
        label="muddy boot",
        phrase="a muddy boot",
        line='A very pooey smell rose from a muddy boot someone had kicked off in a hurry.',
        clue="a brown boot print pointed across the floor",
        startle=1,
        tags={"pooey", "boot"},
    ),
    "old_lunchbox": SmellSource(
        id="old_lunchbox",
        label="old lunchbox",
        phrase="an old lunchbox",
        line='Then a sharp, pooey smell leaked from an old lunchbox that had been forgotten all day.',
        clue="a tiny crumb trail led away from it",
        startle=1,
        tags={"pooey", "lunchbox"},
    ),
}

SPOTS = {
    "doormat": Spot(
        id="doormat",
        label="doormat",
        phrase="under the doormat",
        clue="a bright silver half-circle winked out from under the edge of the mat",
        retrieve="lifted the mat and found the bangle waiting underneath",
        fail="peeked around the mat, but in the rush missed the silver ring tucked under it",
        difficulty=1,
        lost_after_delay=False,
        tags={"mat"},
    ),
    "toy_chest": Spot(
        id="toy_chest",
        label="toy chest",
        phrase="inside the toy chest",
        clue="a faint little clink came from the toy chest when it was nudged",
        retrieve="opened the toy chest and heard the bangle chime against the wooden side",
        fail="opened the lid too fast and only stirred the toys without noticing the soft little clink below",
        difficulty=2,
        lost_after_delay=False,
        tags={"chest"},
    ),
    "flowerpot": Spot(
        id="flowerpot",
        label="flowerpot",
        phrase="behind a flowerpot",
        clue="a thin line in the dust curved behind the flowerpot",
        retrieve="moved the flowerpot gently and found the bangle shining in the dust",
        fail="looked near the pots but not behind them, so the curved dust mark went unnoticed",
        difficulty=2,
        lost_after_delay=False,
        tags={"pot"},
    ),
    "drain_grate": Spot(
        id="drain_grate",
        label="drain grate",
        phrase="beside the drain grate",
        clue="a silver gleam flashed between the wet slats of the grate",
        retrieve="knelt by the grate and hooked the bangle out before the water carried it away",
        fail="heard the rain tapping at the grate, but by the time they guessed there, the bangle had slipped deeper and out of reach",
        difficulty=3,
        lost_after_delay=True,
        tags={"drain"},
    ),
}

METHODS = {
    "clues": SearchMethod(
        id="clues",
        label="follow clues",
        line="They decided to be real detectives and follow every small clue instead of guessing.",
        success="One clue led to the next until the hiding place made sense.",
        failure="They tried to follow clues, but the trail was already too faint and late.",
        power=3,
        sense=3,
        tags={"clues", "detective"},
    ),
    "listen": SearchMethod(
        id="listen",
        label="listen and look slowly",
        line="They stood still, listened for tiny sounds, and looked slowly instead of rushing.",
        success="The quiet search helped them notice what a fast search would miss.",
        failure="They listened carefully, but the place was trickier than they expected.",
        power=2,
        sense=2,
        tags={"listen", "detective"},
    ),
    "guess": SearchMethod(
        id="guess",
        label="make a quick guess",
        line="They made a quick guess and hurried to the nearest corner without checking the clues.",
        success="By rare good luck, the first guess happened to be right.",
        failure="A quick guess felt bold, but it was not careful enough for this mystery.",
        power=1,
        sense=1,
        tags={"guess"},
    ),
}

HELPERS = {
    "mother": {"type": "mother", "name": "Mother"},
    "father": {"type": "father", "name": "Father"},
    "grandmother": {"type": "grandmother", "name": "Grandma"},
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ava", "Elsie", "June", "Zoe", "Maya"]
BOY_NAMES = ["Owen", "Ben", "Milo", "Sam", "Noah", "Finn", "Theo", "Leo"]
TRAITS = ["careful", "curious", "brave", "thoughtful", "quiet", "keen"]


def valid_combo(place_id: str, source_id: str, spot_id: str) -> bool:
    if place_id not in PLACES or source_id not in SOURCES or spot_id not in SPOTS:
        return False
    place = PLACES[place_id]
    return source_id in place.sources and spot_id in place.spots and SOURCES[source_id].startle >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id in sorted(place.sources):
            for spot_id in sorted(place.spots):
                if valid_combo(place_id, source_id, spot_id):
                    out.append((place_id, source_id, spot_id))
    return out


def sensible_methods() -> list[SearchMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def mystery_difficulty(spot: Spot, delay: int) -> int:
    return spot.difficulty + delay


def solved(method: SearchMethod, spot: Spot, delay: int) -> bool:
    return method.power >= mystery_difficulty(spot, delay)


def explain_rejection(place_id: str, source_id: str, spot_id: str) -> str:
    if place_id not in PLACES:
        return "(No story: unknown place.)"
    place = PLACES[place_id]
    if source_id not in SOURCES:
        return "(No story: unknown smell source.)"
    if spot_id not in SPOTS:
        return "(No story: unknown hiding spot.)"
    if source_id not in place.sources:
        return f"(No story: {SOURCES[source_id].phrase} does not fit naturally in {place.phrase}.)"
    if spot_id not in place.spots:
        return f"(No story: a bangle would not plausibly roll to {SPOTS[spot_id].phrase} in {place.phrase}.)"
    return "(No story: this combination is not reasonable.)"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try a careful mystery method such as {better}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    spot = SPOTS[params.spot]
    return "happy" if solved(method, spot, params.delay) else "bad"


def _do_loss(world: World, spot: Spot, delay: int, narrate: bool = True) -> None:
    bangle = world.get("bangle")
    hero = world.get("hero")
    bangle.meters["hidden"] += 1
    bangle.meters["delay"] = float(delay)
    bangle.attrs["spot"] = spot.id
    hero.memes["alarm"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"On a hush-soft afternoon, {hero.id} walked into {place.phrase}. {place.line}"
    )
    world.say(
        f"On {hero.pronoun('possessive')} wrist danced a silver bangle that made a tiny chime with every step."
    )


def love_bangle(world: World, hero: Entity, bangle: Entity) -> None:
    hero.memes["love"] += 1
    bangle.memes["cherished"] += 1
    world.say(
        f"{hero.id} loved that bangle. It was not loud or grand, but it felt like a bright little secret."
    )


def smell_startles(world: World, hero: Entity, source: SmellSource) -> None:
    hero.memes["disgust"] += 1
    world.say(source.line)
    world.say(
        f'{hero.id} wrinkled {hero.pronoun("possessive")} nose. "Pooey," {hero.pronoun()} whispered, and jerked {hero.pronoun("possessive")} hand away from the smell.'
    )


def lose_bangle(world: World, hero: Entity, source: SmellSource, spot: Spot, delay: int) -> None:
    _do_loss(world, spot, delay)
    world.say(
        f"In that one quick shake, the bangle slipped loose, rolled with a tiny clink, and vanished {spot.phrase}."
    )
    world.say(
        f"{hero.id} did not see where it went. {source.clue.capitalize()}, but the clue seemed too small to mean anything yet."
    )


def notice_missing(world: World, hero: Entity) -> None:
    world.say(
        f"A moment later, {hero.id} looked down and gasped. The wrist that had felt bright now felt bare."
    )
    world.say(
        f'"My bangle is gone," {hero.pronoun()} said, and suddenly the quiet place felt full of mystery.'
    )


def call_helper(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} came over at once and knelt beside {hero.id}. "Then we will solve it," {helper.pronoun()} said in a calm voice.'
    )


def predict_clue(world: World, spot: Spot) -> dict:
    return {"clue": spot.clue, "spot": spot.label}


def search_scene(world: World, hero: Entity, helper: Entity, method: SearchMethod, spot: Spot) -> None:
    world.say(method.line)
    pred = predict_clue(world, spot)
    world.facts["predicted_clue"] = pred["clue"]
    hero.memes["curiosity"] += 1
    helper.memes["focus"] += 1
    world.say(
        f'Soon {helper.label_word} noticed one thing, then another. "{pred["clue"][0].upper()}{pred["clue"][1:]}," {helper.pronoun()} murmured.'
    )


def recover(world: World, hero: Entity, helper: Entity, method: SearchMethod, spot: Spot) -> None:
    bangle = world.get("bangle")
    bangle.meters["hidden"] = 0.0
    bangle.meters["found"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    helper.memes["relief"] += 1
    world.say(method.success)
    world.say(
        f'Together they {spot.retrieve}.'
    )
    world.say(
        f'{helper.label_word.capitalize()} slid the cool silver bangle back onto {hero.id}\'s wrist. It gave a soft chime, as if the mystery itself had sighed with relief.'
    )
    world.say(
        f'{hero.id} smiled so wide that even the dim corners did not seem secret anymore.'
    )


def lose_for_now(world: World, hero: Entity, helper: Entity, method: SearchMethod, spot: Spot) -> None:
    bangle = world.get("bangle")
    hero.memes["sadness"] += 1
    hero.memes["worry"] += 1
    helper.memes["care"] += 1
    world.say(method.failure)
    world.say(spot.fail.capitalize() + ".")
    if bangle.meters["far_away"] >= THRESHOLD:
        world.say(
            "Rainwater whispered through the grate, and the silver gleam was gone before they could reach it."
        )
    world.say(
        f'{hero.id} leaned against {helper.label_word} and blinked hard. The mystery had an answer somewhere, but not one they could hold that day.'
    )
    world.say(
        f'"We can keep looking another time," {helper.pronoun()} said softly, but the bare wrist still felt lonely.'
    )


def tell(
    place: Place,
    source: SmellSource,
    spot: Spot,
    method: SearchMethod,
    helper_type: str = "mother",
    hero_name: str = "Lila",
    hero_gender: str = "girl",
    trait: str = "curious",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            attrs={"trait": trait},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
        )
    )
    bangle = world.add(
        Entity(
            id="bangle",
            kind="thing",
            type="bangle",
            label="bangle",
            phrase="a silver bangle",
            attrs={"owner": hero_name},
            tags={"bangle"},
        )
    )

    introduce(world, hero, place)
    love_bangle(world, hero, bangle)

    world.para()
    smell_startles(world, hero, source)
    lose_bangle(world, hero, source, spot, delay)
    notice_missing(world, hero)
    call_helper(world, hero, helper)

    world.para()
    search_scene(world, hero, helper, method, spot)
    if solved(method, spot, delay):
        recover(world, hero, helper, method, spot)
        outcome = "happy"
    else:
        lose_for_now(world, hero, helper, method, spot)
        outcome = "bad"

    world.facts.update(
        hero=hero,
        helper=helper,
        bangle=bangle,
        place=place,
        source=source,
        spot=spot,
        method=method,
        delay=delay,
        outcome=outcome,
        found=bangle.meters["found"] >= THRESHOLD,
        lost=bangle.meters["hidden"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "bangle": [
        (
            "What is a bangle?",
            "A bangle is a hard bracelet that slips over your hand and rests on your wrist. Some jingle softly when you move."
        )
    ],
    "pooey": [
        (
            "What does pooey mean?",
            "Pooey means something smells very bad. People often say it when they wrinkle their nose at a stink."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues and asks what those clues mean. Instead of guessing fast, a detective looks carefully."
        )
    ],
    "drain": [
        (
            "Why can small things get lost near a drain?",
            "A drain has narrow spaces where little objects can slip down. Water can also carry light things farther away."
        )
    ],
    "compost": [
        (
            "Why can compost smell strong?",
            "Compost is made of old food and plant bits breaking down. When that happens, it can make a strong smell."
        )
    ],
    "boot": [
        (
            "Why can a muddy boot smell bad?",
            "Mud can trap wet dirt and old leaves. If the boot stays damp, it can smell quite bad."
        )
    ],
    "lunchbox": [
        (
            "Why can an old lunchbox smell bad?",
            "If food stays in a lunchbox too long, it can spoil. Spoiled food often smells very strong."
        )
    ],
}
KNOWLEDGE_ORDER = ["pooey", "bangle", "detective", "drain", "compost", "boot", "lunchbox"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, place, source, outcome = f["hero"], f["place"], f["source"], f["outcome"]
    prompts = [
        f'Write a short child-friendly mystery story that includes the words "pooey" and "bangle".',
        f"Tell a gentle mystery where {hero.id} loses a beloved bangle after a pooey smell in {place.phrase}, and the search changes the ending.",
        f"Write a simple mystery with a missing bracelet, a clue trail, and a calm helper."
    ]
    if outcome == "bad":
        prompts.append("Give the mystery a sad ending where the lost object is not found that day.")
    else:
        prompts.append("Give the mystery a happy ending where the missing object is found and returned.")
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    source = f["source"]
    spot = f["spot"]
    method = f["method"]
    out = f["outcome"]
    helper_word = helper.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who loves a silver bangle, and {helper_word} who helps solve the mystery. The story happens in {place.phrase}."
        ),
        (
            "Why did the bangle go missing?",
            f"A sudden pooey smell from {source.phrase} made {hero.id} jerk {hero.pronoun('possessive')} hand away. In that quick motion, the bangle slipped off and rolled out of sight."
        ),
        (
            "What made the story feel like a mystery?",
            f"The bangle vanished so fast that nobody saw where it went at first. After that, they had to follow small clues and think carefully about what had happened."
        ),
        (
            f"What clue helped point toward the {spot.label}?",
            f"The clue was that {spot.clue}. That small sign matched the place where the bangle had really gone."
        ),
    ]
    if out == "happy":
        qa.append(
            (
                f"How did {helper_word} help solve the mystery?",
                f"{helper_word.capitalize()} stayed calm and used the method of {method.label}. That careful search was strong enough for this hiding place, so they found the bangle and put it back on {hero.id}'s wrist."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily. The missing bangle was found, the mystery was solved, and the soft chime on {hero.id}'s wrist showed that things were right again."
            )
        )
    else:
        bad_reason = "the hiding place was too tricky for that rushed search"
        if spot.id == "drain_grate" and f["delay"] > 0:
            bad_reason = "the rain and delay let the bangle slip deeper by the drain before they could reach it"
        qa.append(
            (
                "Why did the search fail?",
                f"The search failed because {bad_reason}. They tried, but the clues were not used well enough in time."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly, with the bangle still lost for now. {helper_word.capitalize()} comforted {hero.id}, but the bare wrist showed that the mystery did not have a happy answer that day."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"pooey", "bangle"}
    tags |= set(f["method"].tags)
    tags |= set(f["source"].tags)
    tags |= set(f["spot"].tags)
    if "drain" in tags:
        tags.add("drain")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    source: str
    spot: str
    method: str
    helper: str
    name: str
    gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="porch",
        source="compost_pail",
        spot="doormat",
        method="clues",
        helper="mother",
        name="Lila",
        gender="girl",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        place="hallway",
        source="old_lunchbox",
        spot="toy_chest",
        method="listen",
        helper="father",
        name="Owen",
        gender="boy",
        trait="quiet",
        delay=0,
    ),
    StoryParams(
        place="garden_shed",
        source="compost_pail",
        spot="flowerpot",
        method="clues",
        helper="grandmother",
        name="Mina",
        gender="girl",
        trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        place="porch",
        source="muddy_boot",
        spot="drain_grate",
        method="guess",
        helper="mother",
        name="Ben",
        gender="boy",
        trait="brave",
        delay=1,
    ),
    StoryParams(
        place="hallway",
        source="muddy_boot",
        spot="toy_chest",
        method="guess",
        helper="father",
        name="June",
        gender="girl",
        trait="keen",
        delay=2,
    ),
]


ASP_RULES = r"""
valid(P, S, H) :- place(P), source(S), spot(H), allows_source(P, S), allows_spot(P, H), startle(S, N), N >= 1.

sensible(M) :- method(M), sense(M, V), sense_min(T), V >= T.

difficulty(D) :- chosen_spot(H), spot_difficulty(H, Base), delay(L), D = Base + L.
solved :- chosen_method(M), chosen_spot(H), method_power(M, P), difficulty(D), P >= D.
outcome(happy) :- solved.
outcome(bad) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.sources):
            lines.append(asp.fact("allows_source", pid, sid))
        for hid in sorted(place.spots):
            lines.append(asp.fact("allows_spot", pid, hid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("startle", sid, source.startle))
    for hid, spot in SPOTS.items():
        lines.append(asp.fact("spot", hid))
        lines.append(asp.fact("spot_difficulty", hid, spot.difficulty))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_power", mid, method.power))
        lines.append(asp.fact("sense", mid, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_method", params.method),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sensible = set(asp_sensible_methods())
    if py_sensible == asp_sensible:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=True, qa=True, header="### smoke test")
        finally:
            sys.stdout = old_stdout
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A child-friendly mystery storyworld about a missing bangle and a pooey clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the search waits before really beginning")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.spot and not valid_combo(args.place, args.source, args.spot):
        raise StoryError(explain_rejection(args.place, args.source, args.spot))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        if args.place and args.source and args.spot:
            raise StoryError(explain_rejection(args.place, args.source, args.spot))
        raise StoryError("(No valid combination matches the given options.)")

    place, source, spot = rng.choice(sorted(combos))
    method = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place,
        source=source,
        spot=spot,
        method=method,
        helper=helper,
        name=name,
        gender=gender,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.spot not in SPOTS:
        raise StoryError(f"(No story: unknown spot '{params.spot}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{params.method}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not valid_combo(params.place, params.source, params.spot):
        raise StoryError(explain_rejection(params.place, params.source, params.spot))
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        place=PLACES[params.place],
        source=SOURCES[params.source],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
        helper_type=params.helper,
        hero_name=params.name,
        hero_gender=params.gender,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        print(f"{len(combos)} compatible (place, source, spot) combos:\n")
        for place, source, spot in combos:
            print(f"  {place:12} {source:14} {spot}")
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.source} in {p.place} -> {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
