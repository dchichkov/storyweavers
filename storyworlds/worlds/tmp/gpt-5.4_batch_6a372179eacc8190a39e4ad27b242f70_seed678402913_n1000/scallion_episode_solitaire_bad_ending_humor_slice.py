#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scallion_episode_solitaire_bad_ending_humor_slice.py
================================================================================

A standalone storyworld about a cozy, silly afternoon that goes wrong because
one person tries to eat lunch, watch one more episode, and finish a game of
solitaire at the same time.

Seed words rebuilt as world state
---------------------------------
This world always includes:
- scallion: a chopped garnish on the hot lunch
- episode: the show the hero is eager to watch
- solitaire: the card layout the hero does not want to abandon

Core premise
------------
The hero is at home with a hot lunch and an almost-finished solitaire game.
A favorite episode is starting. Instead of choosing one thing at a time, the
hero balances the bowl too close to the cards while trying to keep watching.
A pet adds one more bump. The lunch spills, and the ending is always bad in a
small, child-readable slice-of-life way: at minimum the lunch is lost and the
episode goes on without the hero; in worse cases the solitaire cards are ruined
too.

Run it
------
    python storyworlds/worlds/gpt-5.4/scallion_episode_solitaire_bad_ending_humor_slice.py
    python storyworlds/worlds/gpt-5.4/scallion_episode_solitaire_bad_ending_humor_slice.py --meal noodles --spot couch_arm --pet cat
    python storyworlds/worlds/gpt-5.4/scallion_episode_solitaire_bad_ending_humor_slice.py --spot kitchen_table
    python storyworlds/worlds/gpt-5.4/scallion_episode_solitaire_bad_ending_humor_slice.py --cleanup tissue
    python storyworlds/worlds/gpt-5.4/scallion_episode_solitaire_bad_ending_humor_slice.py --all
    python storyworlds/worlds/gpt-5.4/scallion_episode_solitaire_bad_ending_humor_slice.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/scallion_episode_solitaire_bad_ending_humor_slice.py --verify
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
    phrase: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Meal:
    id: str
    label: str
    phrase: str
    vessel: str
    spill: int
    garnish_text: str
    landing_text: str
    flopped_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    wobble: int
    near_cards: bool
    setting_line: str
    balance_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PetCfg:
    id: str
    label: str
    phrase: str
    jumpiness: int
    notice_text: str
    chaos_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class EpisodeCfg:
    id: str
    show: str
    kind: str
    hook: str
    opening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cleanup:
    id: str
    label: str
    sense: int
    power: int
    rush_text: str
    save_text: str
    fail_text: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("meal")
    spot = world.get("spot")
    pet = world.get("pet")
    if bowl.meters["perched"] < THRESHOLD:
        return out
    risk = bowl.meters["spill_risk"]
    wobble_need = float(spot.attrs.get("wobble", 0) + pet.attrs.get("jumpiness", 0))
    if risk >= THRESHOLD and wobble_need >= 2:
        sig = ("wobble",)
        if sig not in world.fired:
            world.fired.add(sig)
            bowl.meters["wobbling"] += 1
            out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("meal")
    cards = world.get("cards")
    hero = world.get("hero")
    room = world.get("room")
    if bowl.meters["wobbling"] < THRESHOLD or bowl.meters["tilted"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["spilled"] += 1
    room.meters["mess"] += 1
    hero.memes["alarm"] += 1
    hero.memes["regret"] += 1
    if world.facts.get("cards_nearby"):
        cards.meters["splashed"] += 1
    out.append("__spill__")
    return out


def _r_episode_lost(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("meal")
    hero = world.get("hero")
    screen = world.get("screen")
    if bowl.meters["spilled"] < THRESHOLD:
        return out
    sig = ("episode_lost",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    screen.meters["advanced"] += 1
    hero.meters["missed_episode"] += 1
    hero.memes["frustration"] += 1
    out.append("__episode__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="episode_lost", tag="time", apply=_r_episode_lost),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for item in produced:
            if not item.startswith("__"):
                world.say(item)
    return produced


MEALS = {
    "noodles": Meal(
        id="noodles",
        label="noodles",
        phrase="a warm bowl of noodles with a little shower of scallion on top",
        vessel="bowl",
        spill=2,
        garnish_text="The chopped scallion floated like tiny green commas on the broth.",
        landing_text="The noodles slithered over the edge in one long, rude swoop.",
        flopped_text="One scallion ring landed right on the hero's nose and stayed there.",
        tags={"broth", "scallion", "lunch"},
    ),
    "congee": Meal(
        id="congee",
        label="congee",
        phrase="a bowl of soft congee with sliced scallion and a spoon resting inside",
        vessel="bowl",
        spill=2,
        garnish_text="The scallion circles bobbed on the pale porridge like little rafts.",
        landing_text="The congee slumped out in a hot, slow wave and chased the cards.",
        flopped_text="A brave scallion slice stuck to the hero's sleeve like a tiny green medal.",
        tags={"porridge", "scallion", "lunch"},
    ),
    "tomato_soup": Meal(
        id="tomato_soup",
        label="tomato soup",
        phrase="a bowl of tomato soup with scallion sprinkled across the top",
        vessel="bowl",
        spill=3,
        garnish_text="The scallion made the red soup look very proud of itself.",
        landing_text="The soup rushed out bright and fast, far too interested in the playing cards.",
        flopped_text="A slippery scallion bit clung to the television remote as if it had bought a ticket.",
        tags={"soup", "scallion", "lunch"},
    ),
    "toast": Meal(
        id="toast",
        label="toast",
        phrase="two pieces of toast with a few chopped scallion bits on scrambled egg",
        vessel="plate",
        spill=0,
        garnish_text="The scallion smelled nice, but it sat politely on the toast.",
        landing_text="Nothing much could pour.",
        flopped_text="The toast mostly minded its own business.",
        tags={"toast", "scallion", "lunch"},
    ),
}

SPOTS = {
    "coffee_table": Spot(
        id="coffee_table",
        label="coffee table",
        phrase="the coffee table in front of the couch",
        wobble=1,
        near_cards=True,
        setting_line="A half-finished solitaire game already covered the coffee table in neat, hopeful rows.",
        balance_line="There was just enough room for the bowl if nobody breathed too hard.",
        tags={"table", "cards"},
    ),
    "couch_arm": Spot(
        id="couch_arm",
        label="couch arm",
        phrase="the wide arm of the couch",
        wobble=2,
        near_cards=True,
        setting_line="The solitaire cards spread onto the seat cushion and crept toward the couch arm.",
        balance_line="The couch arm looked wide for one daring second and then looked less wide.",
        tags={"couch", "cards"},
    ),
    "stool": Spot(
        id="stool",
        label="little stool",
        phrase="a little stool pulled too close to the couch",
        wobble=2,
        near_cards=True,
        setting_line="The solitaire cards had spilled from the stool to the floor in a careful crooked fan.",
        balance_line="The stool had one short leg and the manners of a goat.",
        tags={"stool", "cards"},
    ),
    "kitchen_table": Spot(
        id="kitchen_table",
        label="kitchen table",
        phrase="the kitchen table",
        wobble=0,
        near_cards=False,
        setting_line="The kitchen table stood flat and calm, with plenty of room for lunch and not much for drama.",
        balance_line="Nothing on that table was in the mood to tip.",
        tags={"table"},
    ),
}

PETS = {
    "cat": PetCfg(
        id="cat",
        label="cat",
        phrase="the family cat",
        jumpiness=2,
        notice_text="The cat had been pretending not to care, which is often how a cat begins to care very much.",
        chaos_text="Then the cat spotted a twitching scallion ring and launched itself like a fluffy bad idea.",
        tags={"cat", "pet"},
    ),
    "dog": PetCfg(
        id="dog",
        label="dog",
        phrase="the little dog",
        jumpiness=1,
        notice_text="The dog kept thumping its tail every time a card slid into place.",
        chaos_text="Then the dog bounced up to investigate lunch, cards, and excitement all at once.",
        tags={"dog", "pet"},
    ),
    "rabbit": PetCfg(
        id="rabbit",
        label="rabbit",
        phrase="the house rabbit",
        jumpiness=1,
        notice_text="The rabbit sat nearby with the serious face of someone planning mischief in silence.",
        chaos_text="Then the rabbit darted under the stool so fast that everything above it remembered gravity.",
        tags={"rabbit", "pet"},
    ),
}

EPISODES = {
    "baking": EpisodeCfg(
        id="baking",
        show="The Sunny Spoon",
        kind="baking episode",
        hook="Today's episode promised a cake shaped like a moon.",
        opening="The opening song had barely started when the kitchen on the screen filled with glittery sugar clouds.",
        tags={"television", "episode"},
    ),
    "space": EpisodeCfg(
        id="space",
        show="Rocket Pals",
        kind="space episode",
        hook="This episode was the one with the cardboard rocket race.",
        opening="The first scene showed two wobbling astronauts and a beep-beep countdown.",
        tags={"television", "episode"},
    ),
    "detective": EpisodeCfg(
        id="detective",
        show="Button Detective",
        kind="detective episode",
        hook="This was the missing-muffin episode, the best one according to the hero.",
        opening="A tiny detective hat tipped across the screen just as the mystery music began.",
        tags={"television", "episode"},
    ),
}

CLEANUPS = {
    "dish_towel": Cleanup(
        id="dish_towel",
        label="dish towel",
        sense=3,
        power=4,
        rush_text="snatched up a thick dish towel and moved with the speed of someone who had seen lunch try to escape before",
        save_text="The towel caught most of the spill before it could soak all the cards, though lunch was still a complete loss.",
        fail_text="The towel arrived bravely but too late to stop the soup from reaching every royal card in sight.",
        qa_text="used a thick dish towel to stop most of the spill",
        tags={"cleanup", "towel"},
    ),
    "paper_towels": Cleanup(
        id="paper_towels",
        label="paper towels",
        sense=2,
        power=3,
        rush_text="grabbed a long string of paper towels and swooped in",
        save_text="The paper towels saved a few corners of the solitaire layout, but the bowl was gone and the episode kept rolling.",
        fail_text="The paper towels tore and skidded, and the spill marched right through the solitaire rows.",
        qa_text="grabbed paper towels and blotted the spill as fast as possible",
        tags={"cleanup", "paper_towels"},
    ),
    "tiny_tray": Cleanup(
        id="tiny_tray",
        label="tiny tray",
        sense=1,
        power=1,
        rush_text="picked up a tiny tray, which was the wrong size for nearly every part of the problem",
        save_text="The tray did not really save anything except confusion.",
        fail_text="The tray helped nobody and seemed surprised to be invited.",
        qa_text="tried to help with a tiny tray",
        tags={"cleanup"},
    ),
}


def risky_combo(meal: Meal, spot: Spot, pet: PetCfg) -> bool:
    return meal.spill > 0 and spot.near_cards and (spot.wobble + pet.jumpiness) >= 3


def sensible_cleanups() -> list[Cleanup]:
    return [cfg for cfg in CLEANUPS.values() if cfg.sense >= SENSE_MIN]


def severity_of(params: "StoryParams") -> int:
    return MEALS[params.meal].spill + SPOTS[params.spot].wobble + PETS[params.pet].jumpiness


def outcome_of(params: "StoryParams") -> str:
    if CLEANUPS[params.cleanup].power >= severity_of(params):
        return "cards_saved"
    return "cards_ruined"


def explain_rejection(meal: Meal, spot: Spot, pet: PetCfg) -> str:
    if meal.spill <= 0:
        return (
            f"(No story: {meal.phrase} is not a real spill hazard. This world needs a lunch "
            f"that can slosh onto the solitaire cards.)"
        )
    if not spot.near_cards:
        return (
            f"(No story: {spot.phrase} keeps the meal away from the solitaire layout, so the bad ending "
            f"never gets started. Pick a riskier place near the cards.)"
        )
    return (
        f"(No story: {meal.label} near {spot.phrase} with the {pet.label} is not unstable enough for this "
        f"world's comic spill. The trouble needs a wobbly setup and a lively pet.)"
    )


def explain_cleanup(cid: str) -> str:
    cfg = CLEANUPS[cid]
    better = ", ".join(sorted(c.id for c in sensible_cleanups()))
    return (
        f"(Refusing cleanup '{cid}': it scores too low on common sense "
        f"(sense={cfg.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for meal_id, meal in MEALS.items():
        for spot_id, spot in SPOTS.items():
            for pet_id, pet in PETS.items():
                for episode_id in EPISODES:
                    if risky_combo(meal, spot, pet):
                        combos.append((meal_id, spot_id, pet_id, episode_id))
    return combos


@dataclass
class StoryParams:
    meal: str
    spot: str
    pet: str
    episode: str
    cleanup: str
    hero_name: str
    hero_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def predict_spill(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    bowl = sim.get("meal")
    bowl.meters["perched"] += 1
    bowl.meters["spill_risk"] += 1
    hero.memes["distracted"] += 1
    bowl.meters["tilted"] += 1
    propagate(sim, narrate=False)
    cards = sim.get("cards")
    return {
        "spill": bowl.meters["spilled"] >= THRESHOLD,
        "cards_splashed": cards.meters["splashed"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, meal: Meal, spot: Spot, episode: EpisodeCfg) -> None:
    world.say(
        f"After school, {hero.id} came home feeling ordinary and hungry in exactly the same amount."
    )
    world.say(
        f"In the living room waited {meal.phrase}. {meal.garnish_text}"
    )
    world.say(
        f"{spot.setting_line} On television, {episode.show} was about to start. {episode.hook}"
    )
    hero.memes["cozy"] += 1
    world.facts["cards_nearby"] = spot.near_cards


def set_scene(world: World, hero: Entity, spot: Spot, episode: EpisodeCfg) -> None:
    world.say(
        f"{hero.id} had promised to eat first, but then remembered the {episode.kind} and the almost-finished solitaire game."
    )
    world.say(
        f"That is how the bowl ended up on {spot.phrase}. {spot.balance_line}"
    )
    world.say(
        f'"I can do all three," {hero.id} told the room, which was not a room known for objecting.'
    )


def parent_warns(world: World, parent: Entity, hero: Entity) -> None:
    pred = predict_spill(world)
    world.facts["predicted_spill"] = pred["spill"]
    world.facts["predicted_cards"] = pred["cards_splashed"]
    if pred["spill"]:
        world.say(
            f'{parent.label_word.capitalize()} looked in, saw lunch beside solitaire, and said, '
            f'"Pick one thing first, {hero.id}. Bowls and cards do not cooperate."'
        )
        hero.memes["warned"] += 1


def insist(world: World, hero: Entity, episode: EpisodeCfg) -> None:
    hero.memes["greed"] += 1
    world.say(
        f'But {hero.id} only nudged one black card onto one red card and reached for the spoon. "{episode.show} is just one episode," {hero.pronoun()} said. "And solitaire is almost done."'
    )


def pet_notices(world: World, pet: Entity, pet_cfg: PetCfg) -> None:
    world.say(pet_cfg.notice_text)
    pet.memes["interest"] += 1


def trigger_spill(world: World, hero: Entity, pet_cfg: PetCfg, meal: Meal, episode: EpisodeCfg) -> None:
    bowl = world.get("meal")
    bowl.meters["perched"] += 1
    bowl.meters["spill_risk"] += 1
    hero.memes["distracted"] += 1
    world.say(episode.opening)
    world.say(
        f"{hero.id} leaned forward to see better, lifted the spoon, and forgot for one blink that bowls obey gravity more than plans."
    )
    world.say(pet_cfg.chaos_text)
    bowl.meters["tilted"] += 1
    propagate(world, narrate=False)
    world.say(meal.landing_text)
    world.say(meal.flopped_text)


def cleanup_scene(world: World, parent: Entity, cleanup: Cleanup, meal: Meal) -> None:
    cards = world.get("cards")
    parent.meters["cleanup_work"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {cleanup.rush_text}."
    )
    if cards.meters["splashed"] < THRESHOLD:
        world.say(
            f"But the bowl had already burst across the floor. The lunch was gone anyway."
        )
        return
    if cleanup.power >= world.facts["severity"]:
        cards.meters["rescued"] += 1
        world.say(cleanup.save_text)
    else:
        cards.meters["ruined"] += 1
        world.say(cleanup.fail_text)
    world.say(
        f"The apartment smelled like warm {meal.label} and very poor scheduling."
    )


def bad_end_small(world: World, hero: Entity, episode: EpisodeCfg) -> None:
    hero.memes["sad"] += 1
    world.say(
        f"When the floor was finally dry, the {episode.kind} was over. {hero.id} stared at the silent credits and ate crackers instead of lunch."
    )
    world.say(
        f"The solitaire cards survived in a bent little stack, and {hero.id} had learned that " 
        f"wanting everything at once is an excellent way to keep none of it."
    )


def bad_end_big(world: World, hero: Entity, pet: Entity, episode: EpisodeCfg) -> None:
    hero.memes["sad"] += 1
    hero.memes["embarrassed"] += 1
    world.say(
        f"By the time the mess was done being a mess, the {episode.kind} was over and the solitaire cards had curled like tiny disappointed boats."
    )
    world.say(
        f"{hero.id} picked up the queen of hearts from under {pet.label}'s paw and sighed. There would be no winning hand, no hot lunch, and no replay until tomorrow."
    )
    world.say(
        f"The last scallion bit was still clinging to the remote, as if it had enjoyed the whole disaster."
    )


def tell(
    meal: Meal,
    spot: Spot,
    pet_cfg: PetCfg,
    episode: EpisodeCfg,
    cleanup: Cleanup,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "hopeful",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    hero.attrs["name"] = hero_name
    hero.attrs["trait"] = trait
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    pet = world.add(Entity(id="pet", kind="character", type="animal", label=pet_cfg.label, phrase=pet_cfg.phrase, role="pet"))
    pet.attrs["jumpiness"] = pet_cfg.jumpiness
    bowl = world.add(Entity(id="meal", type="meal", label=meal.label, phrase=meal.phrase))
    bowl.attrs["spill"] = meal.spill
    spot_ent = world.add(Entity(id="spot", type="spot", label=spot.label, phrase=spot.phrase))
    spot_ent.attrs["wobble"] = spot.wobble
    cards = world.add(Entity(id="cards", type="cards", label="solitaire cards", phrase="the solitaire cards"))
    screen = world.add(Entity(id="screen", type="screen", label="television", phrase=episode.show))
    world.add(Entity(id="room", type="room", label="living room"))

    introduce(world, hero, meal, spot, episode)
    world.para()
    set_scene(world, hero, spot, episode)
    parent_warns(world, parent, hero)
    insist(world, hero, episode)
    pet_notices(world, pet, pet_cfg)

    world.para()
    trigger_spill(world, hero, pet_cfg, meal, episode)
    severity = meal.spill + spot.wobble + pet_cfg.jumpiness
    world.facts["severity"] = severity

    world.para()
    cleanup_scene(world, parent, cleanup, meal)
    if cleanup.power >= severity:
        outcome = "cards_saved"
        bad_end_small(world, hero, episode)
    else:
        outcome = "cards_ruined"
        bad_end_big(world, hero, pet, episode)

    world.facts.update(
        hero=hero,
        parent=parent,
        pet=pet,
        meal_cfg=meal,
        spot_cfg=spot,
        pet_cfg=pet_cfg,
        episode_cfg=episode,
        cleanup_cfg=cleanup,
        outcome=outcome,
        cards_ruined=world.get("cards").meters["ruined"] >= THRESHOLD,
        cards_saved=world.get("cards").meters["rescued"] >= THRESHOLD,
        episode_missed=world.get("hero").meters["missed_episode"] >= THRESHOLD,
        meal_spilled=world.get("meal").meters["spilled"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "scallion": [
        (
            "What is a scallion?",
            "A scallion is a long green onion with a mild taste. People often slice it into little rings and sprinkle it on food."
        )
    ],
    "episode": [
        (
            "What is an episode?",
            "An episode is one part of a show. It is like one small story inside a bigger series."
        )
    ],
    "solitaire": [
        (
            "What is solitaire?",
            "Solitaire is a card game usually played by one person. You move the cards into careful piles and rows."
        )
    ],
    "cat": [
        (
            "Why do cats knock things over sometimes?",
            "Cats are curious and quick, and they often jump toward anything interesting. If something is balanced badly, a cat can bump it by accident."
        )
    ],
    "dog": [
        (
            "Why can a wagging dog make a mess?",
            "A dog does not have to mean trouble to cause trouble. A wagging tail or sudden bounce can bump things that were not steady."
        )
    ],
    "rabbit": [
        (
            "Why can a rabbit make a stool wobble?",
            "A rabbit can dash under furniture very fast. If the furniture is light or crooked, that quick motion can jostle it."
        )
    ],
    "cleanup": [
        (
            "Why is a thick towel better than one tiny tissue for a spill?",
            "A thick towel can soak up more liquid and stay together while you wipe. One tiny tissue gets soggy too fast and cannot handle a real mess."
        )
    ],
    "broth": [
        (
            "Why is soup harder to balance than toast?",
            "Soup moves inside the bowl, so it can slosh when the bowl tips. Toast mostly stays where it is put."
        )
    ],
}
KNOWLEDGE_ORDER = ["scallion", "episode", "solitaire", "cat", "dog", "rabbit", "cleanup", "broth"]

GIRL_NAMES = ["Mina", "Lila", "June", "Ava", "Lucy", "Nora", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Max", "Theo", "Eli", "Sam", "Noah"]
TRAITS = ["hopeful", "tidy", "greedy", "sleepy", "cheerful", "fussy"]


def hero_name(world: World) -> str:
    return str(world.facts["hero"].attrs.get("name", "The hero"))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    meal = f["meal_cfg"]
    episode = f["episode_cfg"]
    pet = f["pet_cfg"]
    spot = f["spot_cfg"]
    return [
        'Write a funny slice-of-life story for a 3-to-5-year-old that includes the words "scallion", "episode", and "solitaire" and ends badly in a small, everyday way.',
        f"Tell a home story where {hero.attrs['name']} tries to eat {meal.label}, watch one {episode.kind}, and finish solitaire at the same time while the {pet.label} makes things worse.",
        f"Write a gentle comic bad-ending story about a bowl balanced on {spot.phrase}, a favorite episode starting, and a child learning that trying to do everything at once can spoil all of it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    pet = f["pet"]
    meal = f["meal_cfg"]
    spot = f["spot_cfg"]
    episode = f["episode_cfg"]
    cleanup = f["cleanup_cfg"]
    name = hero.attrs["name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, who wanted lunch, solitaire, and one episode all at once, plus {name}'s {pw} and the {pet.label}. The whole trouble began in one very ordinary living room."
        ),
        (
            "Why was the bowl dangerous where it was?",
            f"The bowl was balanced on {spot.phrase}, right beside the solitaire cards. That setup was shaky, and the pet made it even riskier."
        ),
        (
            f"What was on the lunch?",
            f"The lunch had scallion on top. The little green pieces help show that the meal was ready to eat right when {name} tried to do too many things."
        ),
        (
            f"Why did {pw} warn {name}?",
            f"{pw.capitalize()} saw lunch beside the cards and knew bowls and card games do not mix well. The warning came before the spill because the setup already looked unstable."
        ),
        (
            f"What caused the spill?",
            f"{name} leaned forward to watch the {episode.kind}, and then the {pet.label} added one more bump. The bowl tipped because the plan depended on balance and luck at the same time."
        ),
    ]
    if f["outcome"] == "cards_saved":
        qa.append(
            (
                "What bad thing still happened even though some cards were saved?",
                f"The lunch was still lost and the episode finished without {name}. {pw.capitalize()} {cleanup.qa_text}, but that could not bring the hot meal or the missed show back."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended badly but quietly: {name} ate crackers instead of lunch and watched only the credits. The solitaire cards survived, but the afternoon did not go the way {name} wanted."
            )
        )
    else:
        qa.append(
            (
                "What happened to the solitaire cards?",
                f"They were splashed and ruined enough to curl up. The spill reached them before cleanup could stop it."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with no hot lunch, no finished solitaire game, and no full episode. The ruined cards and the scallion on the remote showed exactly how mixed-up the afternoon had become."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"scallion", "episode", "solitaire", "cleanup"}
    tags |= set(f["meal_cfg"].tags)
    tags |= set(f["pet_cfg"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        meal="noodles",
        spot="couch_arm",
        pet="cat",
        episode="detective",
        cleanup="dish_towel",
        hero_name="Mina",
        hero_gender="girl",
        parent="mother",
        trait="hopeful",
    ),
    StoryParams(
        meal="congee",
        spot="stool",
        pet="rabbit",
        episode="space",
        cleanup="paper_towels",
        hero_name="Leo",
        hero_gender="boy",
        parent="father",
        trait="cheerful",
    ),
    StoryParams(
        meal="tomato_soup",
        spot="coffee_table",
        pet="cat",
        episode="baking",
        cleanup="paper_towels",
        hero_name="June",
        hero_gender="girl",
        parent="mother",
        trait="greedy",
    ),
    StoryParams(
        meal="tomato_soup",
        spot="couch_arm",
        pet="dog",
        episode="space",
        cleanup="dish_towel",
        hero_name="Ben",
        hero_gender="boy",
        parent="father",
        trait="fussy",
    ),
]


ASP_RULES = r"""
risky(Meal, Spot, Pet, Episode) :-
    meal(Meal), spot(Spot), pet(Pet), episode(Episode),
    spill(Meal, S), S > 0,
    near_cards(Spot),
    wobble(Spot, W), jumpiness(Pet, J), W + J >= 3.

sensible_cleanup(C) :-
    cleanup(C), sense(C, S), sense_min(M), S >= M.

severity(V) :-
    chosen_meal(M), spill(M, S),
    chosen_spot(Sp), wobble(Sp, W),
    chosen_pet(P), jumpiness(P, J),
    V = S + W + J.

outcome(cards_saved) :-
    chosen_cleanup(C), power(C, P),
    severity(V), P >= V.

outcome(cards_ruined) :-
    chosen_cleanup(C), power(C, P),
    severity(V), P < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for meal_id, meal in MEALS.items():
        lines.append(asp.fact("meal", meal_id))
        lines.append(asp.fact("spill", meal_id, meal.spill))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("wobble", spot_id, spot.wobble))
        if spot.near_cards:
            lines.append(asp.fact("near_cards", spot_id))
    for pet_id, pet in PETS.items():
        lines.append(asp.fact("pet", pet_id))
        lines.append(asp.fact("jumpiness", pet_id, pet.jumpiness))
    for episode_id in EPISODES:
        lines.append(asp.fact("episode", episode_id))
    for cid, cleanup in CLEANUPS.items():
        lines.append(asp.fact("cleanup", cid))
        lines.append(asp.fact("sense", cid, cleanup.sense))
        lines.append(asp.fact("power", cid, cleanup.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show risky/4."))
    return sorted(set(asp.atoms(model, "risky")))


def asp_sensible_cleanups() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_cleanup/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible_cleanup"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_meal", params.meal),
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_pet", params.pet),
            asp.fact("chosen_cleanup", params.cleanup),
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

    py_clean = {c.id for c in sensible_cleanups()}
    asp_clean = set(asp_sensible_cleanups())
    if py_clean == asp_clean:
        print(f"OK: sensible cleanup set matches ({sorted(py_clean)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible cleanup set: python={sorted(py_clean)} clingo={sorted(asp_clean)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "scallion" not in sample.story or "solitaire" not in sample.story or "episode" not in sample.story:
            raise StoryError("Smoke test story missing required seed words or empty output.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a hot lunch, one episode, solitaire, and a comic bad ending."
    )
    ap.add_argument("--meal", choices=MEALS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--episode", choices=EPISODES)
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible bad-ending combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cleanup and CLEANUPS[args.cleanup].sense < SENSE_MIN:
        raise StoryError(explain_cleanup(args.cleanup))

    if args.meal and args.spot and args.pet:
        meal = MEALS[args.meal]
        spot = SPOTS[args.spot]
        pet = PETS[args.pet]
        if not risky_combo(meal, spot, pet):
            raise StoryError(explain_rejection(meal, spot, pet))

    combos = [
        c for c in valid_combos()
        if (args.meal is None or c[0] == args.meal)
        and (args.spot is None or c[1] == args.spot)
        and (args.pet is None or c[2] == args.pet)
        and (args.episode is None or c[3] == args.episode)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    meal, spot, pet, episode = rng.choice(sorted(combos))
    cleanup = args.cleanup or rng.choice(sorted(c.id for c in sensible_cleanups()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        meal=meal,
        spot=spot,
        pet=pet,
        episode=episode,
        cleanup=cleanup,
        hero_name=hero_name,
        hero_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.meal not in MEALS:
        raise StoryError(f"(Unknown meal: {params.meal})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")
    if params.episode not in EPISODES:
        raise StoryError(f"(Unknown episode: {params.episode})")
    if params.cleanup not in CLEANUPS:
        raise StoryError(f"(Unknown cleanup: {params.cleanup})")
    if CLEANUPS[params.cleanup].sense < SENSE_MIN:
        raise StoryError(explain_cleanup(params.cleanup))
    if not risky_combo(MEALS[params.meal], SPOTS[params.spot], PETS[params.pet]):
        raise StoryError(explain_rejection(MEALS[params.meal], SPOTS[params.spot], PETS[params.pet]))

    world = tell(
        meal=MEALS[params.meal],
        spot=SPOTS[params.spot],
        pet_cfg=PETS[params.pet],
        episode=EPISODES[params.episode],
        cleanup=CLEANUPS[params.cleanup],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
        trait=params.trait,
    )

    story_text = world.render().replace("hero", params.hero_name)
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show risky/4.\n#show sensible_cleanup/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible cleanup choices: {', '.join(asp_sensible_cleanups())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (meal, spot, pet, episode) combos:\n")
        for meal, spot, pet, episode in combos:
            print(f"  {meal:12} {spot:12} {pet:8} {episode}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.hero_name}: {p.meal} near {p.spot} with {p.pet} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
