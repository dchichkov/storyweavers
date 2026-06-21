#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hint_finch_grate_cautionary_quest_humor_tall.py
============================================================================

A standalone storyworld about a child on a ridiculous little quest to recover a
lost treasure from a grate. A finch gives a hint, the child faces a tempting but
unsafe shortcut, and a sensible grown-up helps with the right tool.

Features:
- Cautionary: do not tug heavy grates or reach into dark holes
- Quest: the child must recover a treasured object
- Humor: light, child-facing tall-tale exaggeration
- Seed words included naturally: hint, finch, grate
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    size: str = ""
    material: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    helper_spot: str
    finch_spot: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    material: str
    size: str
    boast: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Grate:
    id: str
    label: str
    phrase: str
    openings: str
    danger: str
    beneath: str
    allowed_sizes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    sense: int
    works_on: set[str] = field(default_factory=set)
    materials: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
    hint_text: str = ""
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


def _r_item_trapped(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["trapped"] < THRESHOLD:
        return []
    sig = ("trapped", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["quest"] += 1
    return ["__trapped__"]


def _r_grate_tug(world: World) -> list[str]:
    hero = world.get("hero")
    grate = world.get("grate")
    if grate.meters["rattled"] < THRESHOLD:
        return []
    sig = ("rattle", grate.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["risk"] += 1
    hero.meters["pinch_risk"] += 1
    return ["__rattle__"]


def _r_item_recovered(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["recovered"] < THRESHOLD:
        return []
    sig = ("recovered", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["quest"] = 0.0
    return ["__recovered__"]


CAUSAL_RULES = [
    Rule(name="item_trapped", tag="physical", apply=_r_item_trapped),
    Rule(name="grate_tug", tag="physical", apply=_r_grate_tug),
    Rule(name="item_recovered", tag="physical", apply=_r_item_recovered),
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
        for s in produced:
            world.say(s)
    return produced


def item_fits_grate(item: LostThing, grate: Grate) -> bool:
    return item.size in grate.allowed_sizes


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_works(item: LostThing, grate: Grate, method: Method) -> bool:
    return grate.id in method.works_on and item.material in method.materials


def best_method(item: LostThing, grate: Grate) -> Optional[Method]:
    options = [m for m in sensible_methods() if method_works(item, grate, m)]
    if not options:
        return None
    return max(options, key=lambda m: (m.sense, m.id))


def predicted_recovery(item: LostThing, grate: Grate, method: Method) -> bool:
    return item_fits_grate(item, grate) and method_works(item, grate, method)


def predict_tug(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    grate = sim.get("grate")
    grate.meters["rattled"] += 1
    propagate(sim, narrate=False)
    return {
        "pinch_risk": hero.meters["pinch_risk"],
        "worry": hero.memes["worry"],
    }


def introduce(world: World, hero: Entity, companion: Entity, place: Place, item: LostThing) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"In {place.label}, where even the pigeons seemed to march like drummers, "
        f"{hero.id} set out on what {hero.pronoun()} called {item.boast}."
    )
    world.say(
        f"{companion.id} came along too, because every grand quest needs someone "
        f"to ask sensible questions before the hero does something silly."
    )
    world.say(place.scene)


def show_treasure(world: World, hero: Entity, item: LostThing) -> None:
    world.say(
        f"Tucked in {hero.pronoun('possessive')} hand was {item.phrase}. "
        f"To anyone else it was small, but to {hero.id} it shone like the moon's spare button."
    )


def mishap(world: World, hero: Entity, place: Place, item_ent: Entity, item: LostThing,
           grate_ent: Entity, grate: Grate) -> None:
    hero.memes["surprise"] += 1
    item_ent.meters["trapped"] += 1
    propagate(world)
    world.say(
        f"Then a gust puffed through {place.label} so hard it could nearly have turned pages by itself. "
        f"{item.phrase.capitalize()} slipped, bounced once, twice, and skittered onto {grate.phrase}."
    )
    world.say(
        f"With one tiny clink, it slipped through {grate.openings} and landed {grate.beneath}."
    )


def tempt(world: World, hero: Entity, grate: Grate) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'{hero.id} knelt by the {grate.label}. "I can just yank this grate up," '
        f'{hero.pronoun()} said, puffing up like a parade rooster.'
    )


def warn(world: World, companion: Entity, hero: Entity, grate: Grate) -> None:
    pred = predict_tug(world)
    companion.memes["caution"] += 1
    world.facts["predicted_pinch_risk"] = pred["pinch_risk"]
    world.say(
        f'{companion.id} caught {hero.pronoun("possessive")} sleeve. '
        f'"No, you cannot. {grate.danger}, and a heavy grate can pinch fingers faster than a crab."'
    )


def finch_hint(world: World, finch: Entity, place: Place, method: Method) -> None:
    finch.memes["helpfulness"] += 1
    world.say(
        f"Just then a finch landed on {place.finch_spot}, cocked its tiny head, "
        f"and gave the sort of chirp that sounded suspiciously like a hint."
    )
    world.say(
        f"It hopped once, twice, and then fluttered toward {place.helper_spot}, "
        f"right where {method.hint_text}."
    )


def ignore_hint(world: World, hero: Entity, companion: Entity, grate_ent: Entity, grate: Grate) -> None:
    hero.memes["defiance"] += 1
    grate_ent.meters["rattled"] += 1
    propagate(world, narrate=False)
    hero.meters["scraped"] += 1
    hero.memes["fear"] += 1
    companion.memes["fear"] += 1
    world.say(
        f'But {hero.id} muttered, "I am faster than a finch and stronger than a spoonful of thunder," '
        f'and tugged at the {grate.label} anyway.'
    )
    world.say(
        f"The grate did not budge. It only clanked, wobbled, and nipped {hero.pronoun('possessive')} fingers enough "
        f"to make {hero.pronoun('object')} jump back with a yelp."
    )


def heed_hint(world: World, hero: Entity, companion: Entity, place: Place) -> None:
    hero.memes["good_sense"] += 1
    companion.memes["relief"] += 1
    world.say(
        f"{hero.id} looked at the grate, then at the finch, then at {companion.id}. "
        f"Even a tall-tale hero can count to three."
    )
    world.say(
        f"So the two children followed the bird's hint to {place.helper_spot} instead of touching the grate again."
    )


def fetch_help(world: World, grownup: Entity, method: Method) -> None:
    grownup.memes["calm"] += 1
    world.say(
        f"There they found {grownup.label_word}, who listened without laughing even once, "
        f"though the quest had by then grown in the telling to the size of a mountain."
    )
    world.say(
        f"{grownup.label_word.capitalize()} brought {method.phrase}."
    )


def recover(world: World, grownup: Entity, item_ent: Entity, item: LostThing,
            grate: Grate, method: Method) -> None:
    item_ent.meters["recovered"] += 1
    item_ent.meters["trapped"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{grownup.label_word.capitalize()} {method.text.format(item=item.label, grate=grate.label)}."
    )
    world.say(
        f"Up came {item.phrase}, dusty but safe, as if it had only gone below to practice being mysterious."
    )


def lesson(world: World, grownup: Entity, hero: Entity, companion: Entity, grate: Grate,
           had_scrape: bool) -> None:
    hero.memes["lesson"] += 1
    companion.memes["lesson"] += 1
    world.say(
        f'{grownup.label_word.capitalize()} knelt beside the children. '
        f'"A grate is not a toy or a ladder," {grownup.pronoun()} said. '
        f'"When something drops where hands do not belong, you stop and get help."'
    )
    if had_scrape:
        world.say(
            f"{hero.id} nodded and blew on {hero.pronoun('possessive')} sore fingers. "
            f"The quest had been won, but not by wrestling iron."
        )
    else:
        world.say(
            f"{hero.id} nodded at once, because the object was back and all ten fingers were still smiling."
        )


def ending(world: World, hero: Entity, companion: Entity, finch: Entity, item: LostThing,
           had_scrape: bool) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    if had_scrape:
        world.say(
            f"After that, whenever {hero.id} passed a grate, {hero.pronoun()} gave it plenty of room and a very respectful look."
        )
    else:
        world.say(
            f"After that, {hero.id} liked to boast that the smallest knight on the whole quest had been the finch."
        )
    world.say(
        f"{companion.id} held up {item.label}, the finch flicked its tail, and the afternoon felt bright enough to fit another adventure."
    )


def tell(place: Place, item: LostThing, grate: Grate, method: Method, choice: str,
         hero_name: str = "Milo", hero_type: str = "boy",
         companion_name: str = "Pia", companion_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    companion = world.add(Entity(id="companion", kind="character", type=companion_type, label=companion_name, role="companion"))
    finch = world.add(Entity(id="finch", kind="character", type="bird", label="the finch", role="hint"))
    grownup = world.add(Entity(id="grownup", kind="character", type=parent_type, label="the grown-up", role="helper"))
    item_ent = world.add(Entity(id="item", type="thing", label=item.label, phrase=item.phrase, material=item.material, size=item.size))
    grate_ent = world.add(Entity(id="grate", type="thing", label=grate.label, phrase=grate.phrase))

    hero.id = hero_name
    companion.id = companion_name
    world.entities[hero_name] = world.entities.pop("hero")
    world.entities[companion_name] = world.entities.pop("companion")
    hero = world.get(hero_name)
    companion = world.get(companion_name)
    world.entities["hero"] = hero
    world.entities["companion"] = companion

    introduce(world, hero, companion, place, item)
    show_treasure(world, hero, item)

    world.para()
    mishap(world, hero, place, item_ent, item, grate_ent, grate)
    tempt(world, hero, grate)
    warn(world, companion, hero, grate)
    finch_hint(world, finch, place, method)

    world.para()
    had_scrape = False
    if choice == "ignore":
        ignore_hint(world, hero, companion, grate_ent, grate)
        had_scrape = True
    else:
        heed_hint(world, hero, companion, place)

    fetch_help(world, grownup, method)
    recover(world, grownup, item_ent, item, grate, method)

    world.para()
    lesson(world, grownup, hero, companion, grate, had_scrape)
    ending(world, hero, companion, finch, item, had_scrape)

    outcome = "pinched" if had_scrape else "smooth"
    world.facts.update(
        place=place,
        item_cfg=item,
        grate_cfg=grate,
        method=method,
        choice=choice,
        hero=hero,
        companion=companion,
        finch=finch,
        grownup=grownup,
        item=item_ent,
        grate=grate_ent,
        had_scrape=had_scrape,
        outcome=outcome,
        recovered=item_ent.meters["recovered"] >= THRESHOLD,
    )
    return world


PLACES = {
    "square": Place(
        id="square",
        label="the windy town square",
        scene="The flag on the clock tower snapped so loudly it sounded as if the sky were applauding.",
        helper_spot="the broom-bright maintenance cart by the fountain",
        finch_spot="the lion statue's nose",
        supports={"storm", "fountain"},
        tags={"park"},
    ),
    "orchard": Place(
        id="orchard",
        label="the apple orchard path",
        scene="The apple trees leaned over the path like old aunties listening for gossip.",
        helper_spot="the little shed beside the wheelbarrows",
        finch_spot="the highest crate by the cider press",
        supports={"storm", "cellar"},
        tags={"park"},
    ),
    "fair": Place(
        id="fair",
        label="the fairground lane",
        scene="The striped tents billowed so grandly they looked one sneeze away from sailing to the moon.",
        helper_spot="the booth where the grounds crew kept keys and tools",
        finch_spot="the painted horse's ear",
        supports={"fountain", "cellar"},
        tags={"park"},
    ),
}

ITEMS = {
    "bell": LostThing(
        id="bell",
        label="bell",
        phrase="a brass bell button",
        material="metal",
        size="tiny",
        boast="The Search for the Moon-Bright Bell",
        tags={"metal", "treasure"},
    ),
    "medal": LostThing(
        id="medal",
        label="medal",
        phrase="a tin parade medal",
        material="metal",
        size="small",
        boast="The Thunderous Parade Medal Rescue",
        tags={"metal", "treasure"},
    ),
    "ribbon": LostThing(
        id="ribbon",
        label="ribbon",
        phrase="a red ribbon with a bow like a fish tail",
        material="cloth",
        size="small",
        boast="The Scarlet Ribbon Expedition",
        tags={"cloth", "treasure"},
    ),
    "map": LostThing(
        id="map",
        label="map",
        phrase="a folded paper treasure map",
        material="paper",
        size="tiny",
        boast="The Secret Map of the Seven Sidewalk Seas",
        tags={"paper", "treasure"},
    ),
    "drum": LostThing(
        id="drum",
        label="toy drum",
        phrase="a toy drum with a brave red rim",
        material="wood",
        size="large",
        boast="The Impossible Drum Retrieval",
        tags={"wood", "treasure"},
    ),
}

GRATES = {
    "storm": Grate(
        id="storm",
        label="storm grate",
        phrase="the storm grate",
        openings="the long rain slots",
        danger="Storm drains are dark and deep under the street",
        beneath="on the dry ledge of the drain tunnel",
        allowed_sizes={"tiny", "small"},
        tags={"grate", "storm_drain"},
    ),
    "fountain": Grate(
        id="fountain",
        label="fountain grate",
        phrase="the fountain grate",
        openings="the round bars around the splashing basin",
        danger="Wet stone is slippery around a fountain",
        beneath="in the shallow catch tray below",
        allowed_sizes={"tiny", "small"},
        tags={"grate", "fountain"},
    ),
    "cellar": Grate(
        id="cellar",
        label="cellar grate",
        phrase="the old cellar grate",
        openings="the square iron gaps",
        danger="Cellar grates cover steps that disappear into shadows",
        beneath="on the first dusty stair below",
        allowed_sizes={"tiny", "small"},
        tags={"grate", "cellar"},
    ),
}

METHODS = {
    "magnet": Method(
        id="magnet",
        label="magnet pole",
        phrase="a long magnet pole",
        sense=3,
        works_on={"storm", "fountain"},
        materials={"metal"},
        text="slid the magnet pole through the {grate}, and the {item} clung to it at once",
        qa_text="used a magnet pole to lift the metal item out",
        hint_text="a long magnet pole leaned against the cart",
        tags={"magnet", "tool"},
    ),
    "grabber": Method(
        id="grabber",
        label="grabber",
        phrase="a long litter grabber",
        sense=3,
        works_on={"storm", "fountain", "cellar"},
        materials={"metal", "cloth", "paper"},
        text="reached in with the litter grabber and pinched the {item} carefully before lifting it past the bars of the {grate}",
        qa_text="used a long grabber to pinch the item and lift it out",
        hint_text="a long grabber hung beside the keys",
        tags={"grabber", "tool"},
    ),
    "key": Method(
        id="key",
        label="maintenance key",
        phrase="a ring of maintenance keys",
        sense=2,
        works_on={"cellar"},
        materials={"metal", "cloth", "paper"},
        text="unlocked the edge of the {grate}, opened it just enough, and picked up the {item} safely",
        qa_text="used a maintenance key to open the grate safely and get the item",
        hint_text="a ring of maintenance keys winked in the sun",
        tags={"key", "tool"},
    ),
    "yank": Method(
        id="yank",
        label="bare hands",
        phrase="bare hands",
        sense=0,
        works_on={"storm", "fountain", "cellar"},
        materials={"metal", "cloth", "paper", "wood"},
        text="tried to pull at the {grate} with bare hands",
        qa_text="tried to yank the grate with bare hands",
        hint_text="nothing sensible at all waited there",
        tags={"unsafe"},
    ),
}


@dataclass
class StoryParams:
    place: str
    item: str
    grate: str
    method: str
    choice: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    parent_type: str
    seed: Optional[int] = None


GIRL_NAMES = ["Pia", "Mina", "Lulu", "Tess", "Ada", "Nora", "Ivy", "June"]
BOY_NAMES = ["Milo", "Otis", "Theo", "Ben", "Max", "Eli", "Finn", "Jude"]


KNOWLEDGE = {
    "finch": [
        (
            "What is a finch?",
            "A finch is a small bird with a quick hop and a sharp little beak. Many finches chirp brightly and move fast from branch to branch."
        )
    ],
    "grate": [
        (
            "What is a grate?",
            "A grate is a heavy metal cover with bars or slots. It lets water or air pass through while keeping people from falling into the space below."
        )
    ],
    "storm_drain": [
        (
            "Why should children stay away from storm drains?",
            "Storm drains are not for playing. They can be deep, dirty, and hard to climb out of, so a grown-up should handle anything that drops there."
        )
    ],
    "fountain": [
        (
            "Why can a fountain edge be slippery?",
            "Water splashes onto the stone around a fountain. Wet stone can make feet slide, so it is safer to walk carefully there."
        )
    ],
    "cellar": [
        (
            "Why is a cellar grate dangerous to play on?",
            "A cellar grate covers steps or a space below. Fingers, toes, or toys can get caught there, so it is not a safe place for a game."
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet can pull some metal things toward it. That makes it handy for picking up small metal objects without reaching into a tight place."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that pinches or holds something from far away. It helps a grown-up reach safely without putting hands into a risky spot."
        )
    ],
    "key": [
        (
            "Why does a grown-up use a key instead of tugging a grate?",
            "A key opens the grate the right way. Tugging a heavy grate can hurt fingers, but opening it carefully is safer."
        )
    ],
    "hint": [
        (
            "What is a hint?",
            "A hint is a small clue that helps you figure something out. It does not solve the whole problem for you, but it points the way."
        )
    ],
}
KNOWLEDGE_ORDER = ["hint", "finch", "grate", "storm_drain", "fountain", "cellar", "magnet", "grabber", "key"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for grate_id, grate in GRATES.items():
            if grate_id not in place.supports:
                continue
            for item_id, item in ITEMS.items():
                if not item_fits_grate(item, grate):
                    continue
                if best_method(item, grate) is not None:
                    combos.append((place_id, item_id, grate_id))
    return combos


def explain_rejection(place: Place, item: LostThing, grate: Grate) -> str:
    if grate.id not in place.supports:
        return (
            f"(No story: {place.label} does not have {grate.phrase}, so this quest setup does not make sense there.)"
        )
    if not item_fits_grate(item, grate):
        return (
            f"(No story: {item.phrase} is too big to slip through {grate.phrase}. "
            f"If nothing can fall through, there is no honest grate problem.)"
        )
    if best_method(item, grate) is None:
        return (
            f"(No story: this world has no sensible way to recover {item.phrase} from {grate.phrase}. "
            f"A cautionary quest needs a believable safe solution.)"
        )
    return "(No story: this combination is unreasonable.)"


def explain_method(item: LostThing, grate: Grate, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Try a safer tool.)"
        )
    if not method_works(item, grate, method):
        return (
            f"(No story: {method.phrase} does not sensibly recover {item.phrase} from {grate.phrase}.)"
        )
    return "(No story: unreasonable method.)"


def outcome_of(params: StoryParams) -> str:
    return "pinched" if params.choice == "ignore" else "smooth"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    item = f["item_cfg"]
    grate = f["grate_cfg"]
    outcome = f["outcome"]
    if outcome == "pinched":
        return [
            f'Write a funny tall-tale story for a 3-to-5-year-old that includes the words "hint", "finch", and "grate".',
            f"Tell a cautionary quest where {hero.id} ignores a finch's hint, tugs at a {grate.label}, gets a small scare, and then learns to get help.",
            f"Write a playful story where {companion.id} gives good advice, a grown-up uses the right tool, and the ending teaches children not to pull heavy grates.",
        ]
    return [
        f'Write a funny tall-tale story for a 3-to-5-year-old that includes the words "hint", "finch", and "grate".',
        f"Tell a quest where {hero.id} loses {item.phrase} through a {grate.label}, follows a finch's hint, and gets help the safe way.",
        f"Write a child-facing cautionary story with a bright ending, where a sensible friend and a helpful grown-up stop a risky shortcut.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    grownup = f["grownup"]
    item = f["item_cfg"]
    grate = f["grate_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {companion.id}, a helpful finch, and a grown-up who helped with the quest."
        ),
        (
            f"What was {hero.id} trying to get back?",
            f"{hero.id} was trying to get back {item.phrase}. It felt very special, so losing it turned the afternoon into a big little quest."
        ),
        (
            f"Why was the grate dangerous?",
            f"The {grate.label} covered a risky space below, so it was not safe to tug or reach into. A heavy grate can pinch fingers, and the hole under it was not a place for children to climb."
        ),
        (
            "What hint did the finch give?",
            f"The finch hopped toward {world.facts['place'].helper_spot}, where {method.hint_text}. The bird did not talk, but its hopping pointed the children toward help."
        ),
    ]
    if outcome == "pinched":
        qa.append(
            (
                f"What happened when {hero.id} ignored the hint?",
                f"{hero.id} tugged at the grate and got a small pinch and a scare. That showed why the shortcut was a bad idea before the grown-up stepped in."
            )
        )
    else:
        qa.append(
            (
                f"What did {hero.id} do when {companion.id} and the finch warned {hero.pronoun('object')}?",
                f"{hero.id} stopped trying to pull the grate and followed the hint instead. That choice kept the quest exciting without making it dangerous."
            )
        )
    qa.append(
        (
            f"How did the grown-up get the item back?",
            f"{grownup.label_word.capitalize()} {method.qa_text}. The safe tool reached the item without anyone having to wrestle the grate."
        )
    )
    qa.append(
        (
            "What did the children learn?",
            f"They learned that a grate is not something to pull on for fun, and that asking for help is smarter than grabbing at danger. The story ends happily because they switched from rushing to thinking."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hint", "finch", "grate"}
    tags |= set(world.facts["grate_cfg"].tags)
    tags |= set(world.facts["method"].tags)
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
        if e.id in {"hero", "companion"}:
            continue
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.material:
            bits.append(f"material={e.material}")
        if e.size:
            bits.append(f"size={e.size}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    hero = world.facts.get("hero")
    companion = world.facts.get("companion")
    if hero is not None:
        lines.append(f"  hero={hero.id} meters={dict((k, v) for k, v in hero.meters.items() if v)} memes={dict((k, v) for k, v in hero.memes.items() if v)}")
    if companion is not None:
        lines.append(f"  companion={companion.id} memes={dict((k, v) for k, v in companion.memes.items() if v)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="square",
        item="bell",
        grate="storm",
        method="magnet",
        choice="heed",
        hero_name="Milo",
        hero_type="boy",
        companion_name="Pia",
        companion_type="girl",
        parent_type="mother",
    ),
    StoryParams(
        place="orchard",
        item="map",
        grate="cellar",
        method="key",
        choice="ignore",
        hero_name="Nora",
        hero_type="girl",
        companion_name="Theo",
        companion_type="boy",
        parent_type="father",
    ),
    StoryParams(
        place="fair",
        item="ribbon",
        grate="cellar",
        method="key",
        choice="heed",
        hero_name="Ada",
        hero_type="girl",
        companion_name="Finn",
        companion_type="boy",
        parent_type="mother",
    ),
    StoryParams(
        place="square",
        item="medal",
        grate="fountain",
        method="magnet",
        choice="ignore",
        hero_name="Otis",
        hero_type="boy",
        companion_name="June",
        companion_type="girl",
        parent_type="father",
    ),
    StoryParams(
        place="fair",
        item="map",
        grate="fountain",
        method="grabber",
        choice="heed",
        hero_name="Ivy",
        hero_type="girl",
        companion_name="Ben",
        companion_type="boy",
        parent_type="mother",
    ),
]


ASP_RULES = r"""
valid(P, I, G) :- place(P), item(I), grate(G), supports(P, G), fits(I, G), recoverable(I, G).
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
recoverable(I, G) :- sensible(M), works(M, G), material_ok(M, I).
outcome(pinched) :- choice(ignore).
outcome(smooth) :- choice(heed).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for gid in GRATES:
        lines.append(asp.fact("grate", gid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        for g in sorted(method.works_on):
            lines.append(asp.fact("works", mid, g))
    for pid, place in PLACES.items():
        for g in sorted(place.supports):
            lines.append(asp.fact("supports", pid, g))
    for iid, item in ITEMS.items():
        for gid, grate in GRATES.items():
            if item_fits_grate(item, grate):
                lines.append(asp.fact("fits", iid, gid))
        for mid, method in METHODS.items():
            if item.material in method.materials:
                lines.append(asp.fact("material_ok", mid, iid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("choice", params.choice)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sense = set(asp_sensible())
    python_sense = {m.id for m in sensible_methods()}
    if clingo_sense == python_sense:
        print(f"OK: sensible methods match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH in outcomes: {len(mismatches)} cases differed.")
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a finch's hint, a dangerous grate, and a silly tall-tale quest."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--grate", choices=GRATES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--choice", choices=["heed", "ignore"])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.grate:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        grate = GRATES[args.grate]
        if (args.place, args.item, args.grate) not in valid_combos():
            raise StoryError(explain_rejection(place, item, grate))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.item is None or c[1] == args.item)
        and (args.grate is None or c[2] == args.grate)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, grate_id = rng.choice(sorted(combos))
    place = PLACES[place_id]
    item = ITEMS[item_id]
    grate = GRATES[grate_id]

    if args.method is not None:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN or not method_works(item, grate, method):
            raise StoryError(explain_method(item, grate, method))
        method_id = args.method
    else:
        compatible = [m.id for m in sensible_methods() if method_works(item, grate, m)]
        if not compatible:
            raise StoryError(explain_rejection(place, item, grate))
        method_id = rng.choice(sorted(compatible))

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or pick_name(rng, hero_type)
    companion_name = args.companion_name or pick_name(rng, companion_type, avoid=hero_name)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    choice = args.choice or rng.choice(["heed", "heed", "ignore"])

    return StoryParams(
        place=place_id,
        item=item_id,
        grate=grate_id,
        method=method_id,
        choice=choice,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        item = ITEMS[params.item]
        grate = GRATES[params.grate]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if (params.place, params.item, params.grate) not in valid_combos():
        raise StoryError(explain_rejection(place, item, grate))
    if method.sense < SENSE_MIN or not method_works(item, grate, method):
        raise StoryError(explain_method(item, grate, method))
    if params.choice not in {"heed", "ignore"}:
        raise StoryError("(Invalid choice: expected 'heed' or 'ignore'.)")

    world = tell(
        place=place,
        item=item,
        grate=grate,
        method=method,
        choice=params.choice,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        companion_name=params.companion_name,
        companion_type=params.companion_type,
        parent_type=params.parent_type,
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
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, grate) combos:\n")
        for place, item, grate in combos:
            print(f"  {place:8} {item:8} {grate}")
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
            header = f"### {p.hero_name}: {p.item} at {p.place} by {p.grate} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
