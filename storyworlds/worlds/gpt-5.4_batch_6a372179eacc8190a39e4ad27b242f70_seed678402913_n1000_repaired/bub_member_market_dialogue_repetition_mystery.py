#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bub_member_market_dialogue_repetition_mystery.py
============================================================================

A standalone story world for a tiny child-facing mystery set at a market.

Seed requirements rebuilt as a simulation:
- words: "bub", "member"
- setting: market
- features: dialogue, repetition
- style: mystery

The world models a small market puzzle:
a child notices that a useful market item is missing, hears a repeating clue,
follows that clue to a plausible hiding place, and discovers what really
happened. The story is gentle rather than scary: the "mystery" is solved by
observation, asking, and checking under or inside ordinary things.

Run it
------
    python storyworlds/worlds/gpt-5.4/bub_member_market_dialogue_repetition_mystery.py
    python storyworlds/worlds/gpt-5.4/bub_member_market_dialogue_repetition_mystery.py --stall bakery
    python storyworlds/worlds/gpt-5.4/bub_member_market_dialogue_repetition_mystery.py --missing member_badge
    python storyworlds/worlds/gpt-5.4/bub_member_market_dialogue_repetition_mystery.py --all
    python storyworlds/worlds/gpt-5.4/bub_member_market_dialogue_repetition_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bub_member_market_dialogue_repetition_mystery.py --json
    python storyworlds/worlds/gpt-5.4/bub_member_market_dialogue_repetition_mystery.py --verify
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
# This file lives in storyworlds/worlds/gpt-5.4/, so we need to add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Shared entity model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
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


# ---------------------------------------------------------------------------
# Domain configuration.
# ---------------------------------------------------------------------------
@dataclass
class Stall:
    id: str
    label: str
    keeper_label: str
    goods: str
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    use: str
    owner_role: str
    fits_places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HidePlace:
    id: str
    label: str
    phrase: str
    clue_sound: str
    clue_line: str
    reveal_text: str
    under: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    actor_type: str
    actor_label: str
    action_text: str
    fix_text: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    calm_line: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    item = world.entities.get("missing")
    hero = world.entities.get("hero")
    keeper = world.entities.get("keeper")
    if not item or not hero or not keeper:
        return []
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    hero.memes["concern"] += 1
    keeper.memes["concern"] += 1
    return ["__missing__"]


def _r_sound_clue(world: World) -> list[str]:
    hero = world.entities.get("hero")
    clue = world.entities.get("clue")
    if not hero or not clue:
        return []
    if clue.meters["heard"] < THRESHOLD:
        return []
    sig = ("sound", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["focus"] += 1
    return ["__sound__"]


def _r_found_relief(world: World) -> list[str]:
    item = world.entities.get("missing")
    hero = world.entities.get("hero")
    keeper = world.entities.get("keeper")
    if not item or not hero or not keeper:
        return []
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    keeper.memes["relief"] += 1
    hero.memes["pride"] += 1
    return ["__found__"]


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="sound_clue", tag="perception", apply=_r_sound_clue),
    Rule(name="found_relief", tag="social", apply=_r_found_relief),
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


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def item_can_hide_in_place(item: MissingItem, place: HidePlace) -> bool:
    return place.id in item.fits_places


def cause_matches_place(cause: Cause, place: HidePlace) -> bool:
    if cause.id == "kitten_nudge":
        return place.id in {"crate_gap", "basket_under_cloth"}
    if cause.id == "wind_slide":
        return place.id in {"crate_gap", "paper_stack"}
    if cause.id == "baby_drop":
        return place.id in {"basket_under_cloth", "paper_stack"}
    return False


def valid_combo(stall_id: str, missing_id: str, place_id: str, cause_id: str) -> bool:
    return (
        item_can_hide_in_place(MISSING_ITEMS[missing_id], HIDING_PLACES[place_id])
        and cause_matches_place(CAUSES[cause_id], HIDING_PLACES[place_id])
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for stall_id in STALLS:
        for missing_id in MISSING_ITEMS:
            for place_id in HIDING_PLACES:
                for cause_id in CAUSES:
                    if valid_combo(stall_id, missing_id, place_id, cause_id):
                        combos.append((stall_id, missing_id, place_id, cause_id))
    return combos


# ---------------------------------------------------------------------------
# Silent prediction helpers.
# ---------------------------------------------------------------------------
def predict_search(place: HidePlace, missing: MissingItem, cause: Cause) -> dict:
    return {
        "findable": item_can_hide_in_place(missing, place) and cause_matches_place(cause, place),
        "reason": cause.action_text.replace("{place}", place.label).replace("{item}", missing.label),
    }


# ---------------------------------------------------------------------------
# Story actions.
# ---------------------------------------------------------------------------
def scene_open(world: World, hero: Entity, grownup: Entity, stall: Stall) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"On market morning, {hero.id} walked between bright stalls with "
        f"{hero.pronoun('possessive')} {grownup.label_word}. The {stall.label} stall "
        f"was full of {stall.goods}, and {stall.smell} drifted through the air."
    )


def meet_keeper(world: World, keeper: Entity, stall: Stall, missing: MissingItem) -> None:
    world.say(
        f"At the stall stood {keeper.id}, the {stall.keeper_label}. A little space "
        f"on the table looked wrong."
    )
    world.say(
        f'"Oh dear," said {keeper.id}. "My {missing.label} is gone, and I need it '
        f'to {missing.use}."'
    )


def hero_notices(world: World, hero: Entity, missing_ent: Entity) -> None:
    missing_ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} blinked at the neat table and then at the empty spot. "
        f"A tiny market mystery had begun."
    )
    world.say(
        f'"Gone?" asked {hero.id}. "{missing_ent.label.capitalize()} gone?"'
    )


def helper_arrives(world: World, helper: Entity, hero: Entity) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"A market member in a green apron was nearby, and everyone called "
        f"{helper.pronoun('object')} {helper.id}."
    )
    world.say(f'"{helper.attrs["line"]}" said {helper.id}.')


def hear_clue(world: World, hero: Entity, place: HidePlace) -> None:
    clue = world.get("clue")
    clue.meters["heard"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then, a small sound came from {place.phrase}: "
        f'"{place.clue_sound}. {place.clue_sound}."'
    )
    world.say(
        f'{hero.id} held still. "{place.clue_line}" {hero.pronoun()} whispered.'
    )


def repeat_guess(world: World, hero: Entity, place: HidePlace) -> None:
    world.say(
        f'"Not there. Maybe there," said {hero.id}. Then {hero.pronoun()} listened '
        f"again: \"{place.clue_sound}. {place.clue_sound}.\""
    )


def search_place(world: World, hero: Entity, helper: Entity, place: HidePlace,
                 missing: MissingItem, cause: Cause) -> None:
    pred = predict_search(place, missing, cause)
    world.facts["predicted_findable"] = pred["findable"]
    world.facts["predicted_reason"] = pred["reason"]
    world.say(
        f'{helper.id} knelt beside {hero.id}. "Shall we check {place.phrase}?" '
        f'{helper.pronoun()} asked.'
    )
    if place.under:
        world.say(
            f"Together they lifted the cloth and peeped underneath."
        )
    else:
        world.say(
            f"Together they leaned close and peeped inside."
        )


def reveal(world: World, keeper: Entity, place: HidePlace, missing: MissingItem,
           cause: Cause) -> None:
    missing_ent = world.get("missing")
    missing_ent.meters["found"] += 1
    propagate(world, narrate=False)
    actor = world.get("cause_actor")
    world.say(place.reveal_text.format(item=missing.label))
    world.say(
        cause.action_text.replace("{place}", place.label).replace("{item}", missing.label)
    )
    world.say(
        f'"So that was it," said {keeper.id}. "{actor.id} did not mean to make trouble."'
    )


def close_story(world: World, hero: Entity, grownup: Entity, keeper: Entity,
                helper: Entity, missing: MissingItem) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f'{keeper.id} smiled and tucked the {missing.label} back where it belonged. '
        f'"Mystery solved," {keeper.pronoun()} said.'
    )
    world.say(
        f'"You listened before you guessed," said {helper.id}. "{helper.attrs["praise"]}"'
    )
    world.say(
        f"{hero.id} grinned at {grownup.pronoun('object')}. The market no longer felt "
        f"full of questions. It felt bright again, and the only thing left was the soft "
        f"busy murmur of morning."
    )


# ---------------------------------------------------------------------------
# Full screenplay.
# ---------------------------------------------------------------------------
def tell(stall: Stall, missing: MissingItem, place: HidePlace, cause: Cause,
         helper_cfg: Helper, hero_name: str = "Nora", hero_gender: str = "girl",
         grownup_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        label=hero_name,
        traits=["careful", "curious"],
    ))
    grownup = world.add(Entity(
        id="Parent",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the parent",
    ))
    keeper = world.add(Entity(
        id="Mira",
        kind="character",
        type="woman",
        role="keeper",
        label=stall.keeper_label,
        attrs={"stall": stall.id},
    ))
    helper = world.add(Entity(
        id=helper_cfg.label,
        kind="character",
        type="person",
        role="helper",
        label=helper_cfg.label,
        attrs={"line": helper_cfg.calm_line, "praise": "That is how good helpers solve little mysteries."},
        tags=set(helper_cfg.tags),
    ))
    actor = world.add(Entity(
        id={"kitten_nudge": "Pip", "wind_slide": "Wind", "baby_drop": "Bub"}[cause.id],
        kind="character" if cause.actor_type != "wind" else "thing",
        type={"kitten": "animal", "wind": "thing", "baby": "boy"}[cause.actor_type],
        role="cause_actor",
        label=cause.actor_label,
    ))
    missing_ent = world.add(Entity(
        id="missing",
        kind="thing",
        type="object",
        label=missing.label,
        phrase=missing.phrase,
        role="missing",
        tags=set(missing.tags),
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="sound",
        label=place.clue_sound,
        role="clue",
        tags=set(place.tags),
    ))
    world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        phrase=place.phrase,
        role="place",
        tags=set(place.tags),
    ))

    scene_open(world, hero, grownup, stall)
    meet_keeper(world, keeper, stall, missing)
    hero_notices(world, hero, missing_ent)

    world.para()
    helper_arrives(world, helper, hero)
    hear_clue(world, hero, place)
    repeat_guess(world, hero, place)
    search_place(world, hero, helper, place, missing, cause)

    world.para()
    reveal(world, keeper, place, missing, cause)
    close_story(world, hero, grownup, keeper, helper, missing)

    world.facts.update(
        hero=hero,
        grownup=grownup,
        keeper=keeper,
        helper=helper,
        cause_actor=actor,
        stall=stall,
        missing_cfg=missing,
        hide_cfg=place,
        cause_cfg=cause,
        missing_ent=missing_ent,
        found=missing_ent.meters["found"] >= THRESHOLD,
        mystery_kind="missing item",
        repeated_sound=place.clue_sound,
    )
    return world


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
STALLS = {
    "bakery": Stall(
        id="bakery",
        label="bakery",
        keeper_label="bread seller",
        goods="round loaves and little buns",
        smell="a warm sweet smell",
        tags={"bread", "market"},
    ),
    "fruit": Stall(
        id="fruit",
        label="fruit stall",
        keeper_label="fruit seller",
        goods="oranges, pears, and shiny apples",
        smell="a fresh juicy smell",
        tags={"fruit", "market"},
    ),
    "flower": Stall(
        id="flower",
        label="flower stall",
        keeper_label="flower seller",
        goods="daisies, sunflowers, and bundles of mint",
        smell="a green clean smell",
        tags={"flower", "market"},
    ),
}

MISSING_ITEMS = {
    "member_badge": MissingItem(
        id="member_badge",
        label="member badge",
        phrase="the little brass member badge",
        use="show which stall belonged to the market member circle",
        owner_role="keeper",
        fits_places={"crate_gap", "basket_under_cloth", "paper_stack"},
        tags={"member", "badge"},
    ),
    "coin_pouch": MissingItem(
        id="coin_pouch",
        label="coin pouch",
        phrase="the striped coin pouch",
        use="make change for customers",
        owner_role="keeper",
        fits_places={"crate_gap", "basket_under_cloth"},
        tags={"coins", "market"},
    ),
    "recipe_card": MissingItem(
        id="recipe_card",
        label="recipe card",
        phrase="the flour-dusted recipe card",
        use="remember the day's special bread",
        owner_role="keeper",
        fits_places={"paper_stack", "basket_under_cloth"},
        tags={"card", "bread"},
    ),
}

HIDING_PLACES = {
    "crate_gap": HidePlace(
        id="crate_gap",
        label="the gap behind a wooden crate",
        phrase="the gap behind a wooden crate",
        clue_sound="bub, bub",
        clue_line="That sound keeps hopping from the crate",
        reveal_text="There, in the shade behind the crate, lay the {item}.",
        under=False,
        tags={"crate", "market"},
    ),
    "basket_under_cloth": HidePlace(
        id="basket_under_cloth",
        label="the basket under the checked cloth",
        phrase="the basket under the checked cloth",
        clue_sound="bub, bub",
        clue_line="The cloth moved when the sound came",
        reveal_text="Inside the basket, under the cloth, was the {item}.",
        under=True,
        tags={"basket", "market"},
    ),
    "paper_stack": HidePlace(
        id="paper_stack",
        label="the stack of brown paper bags",
        phrase="the stack of brown paper bags",
        clue_sound="bub, bub",
        clue_line="The paper fluttered every time the sound came",
        reveal_text="Between two paper bags, flat but safe, rested the {item}.",
        under=False,
        tags={"paper_bag", "market"},
    ),
}

CAUSES = {
    "kitten_nudge": Cause(
        id="kitten_nudge",
        label="kitten nudge",
        actor_type="kitten",
        actor_label="a kitten",
        action_text="A small kitten had batted at the edge of the table and nudged the {item} toward {place}.",
        fix_text="The kitten was lifted away and the stall was tidied.",
        tags={"kitten", "gentle"},
    ),
    "wind_slide": Cause(
        id="wind_slide",
        label="wind slide",
        actor_type="wind",
        actor_label="the wind",
        action_text="A breezy puff had slipped under the paper and pushed the {item} toward {place}.",
        fix_text="The papers were tucked under a jar so the wind could not move them again.",
        tags={"wind", "gentle"},
    ),
    "baby_drop": Cause(
        id="baby_drop",
        label="baby drop",
        actor_type="baby",
        actor_label="a baby nicknamed Bub",
        action_text="A baby named Bub had reached up, patted the table, and dropped the {item} toward {place}.",
        fix_text="Bub was given a wooden spoon to hold instead of reaching for the stall things.",
        tags={"bub", "gentle"},
    ),
}

HELPERS = {
    "porter": Helper(
        id="porter",
        label="Toma",
        calm_line="Slow eyes solve fast worries.",
        tags={"helper", "market_member"},
    ),
    "guard": Helper(
        id="guard",
        label="Rafi",
        calm_line="The market tells its secrets if we listen.",
        tags={"helper", "market_member"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ava", "Zoe", "Ella", "Rose", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Max", "Finn", "Eli", "Theo", "Noah"]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    stall: str
    missing: str
    hiding_place: str
    cause: str
    helper: str
    hero_name: str
    hero_gender: str
    grownup: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "market": [
        (
            "What is a market?",
            "A market is a place where people set up stalls to sell food, flowers, and other things. Many different sellers and shoppers share the same busy space."
        )
    ],
    "member": [
        (
            "What is a member?",
            "A member is someone who belongs to a group. In a market, a member might belong to a sellers' circle or club."
        )
    ],
    "badge": [
        (
            "What does a badge do?",
            "A badge is a small sign or tag that shows something important, like who belongs somewhere. It helps people know what a person or place is connected to."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle when you do not know the answer yet. You solve it by noticing clues and thinking carefully."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a little hint that helps you find an answer. A sound, a footprint, or a moving cloth can all be clues."
        )
    ],
    "kitten": [
        (
            "Why do kittens knock things by accident?",
            "Kittens are curious and playful, so they bat at things with their paws. They usually do not mean to make a mess."
        )
    ],
    "wind": [
        (
            "How can wind move light things?",
            "Wind pushes on light paper and loose objects. A strong puff can slide them across a table or floor."
        )
    ],
    "paper_bag": [
        (
            "Why do paper bags rustle?",
            "Paper bags rustle because dry paper bends and rubs together. That makes a soft crinkly sound."
        )
    ],
    "basket": [
        (
            "What is a basket for?",
            "A basket holds things so they can be carried or kept together. At a market, baskets often hold food or paper."
        )
    ],
    "coins": [
        (
            "What is a coin pouch?",
            "A coin pouch is a small bag for keeping coins together. Sellers use it so money does not roll away."
        )
    ],
}
KNOWLEDGE_ORDER = ["market", "member", "badge", "mystery", "clue", "kitten", "wind",
                   "paper_bag", "basket", "coins"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    stall = f["stall"]
    missing = f["missing_cfg"]
    cause = f["cause_cfg"]
    place = f["hide_cfg"]
    return [
        'Write a short mystery story for a 3-to-5-year-old set in a market that includes the words "bub" and "member".',
        f"Tell a gentle market mystery where {hero.id} hears a repeated sound -- "
        f'"{place.clue_sound}. {place.clue_sound}." -- and uses it to find a missing {missing.label}.',
        f"Write a child-facing story with lots of dialogue, a repeating clue, and a kind ending where the missing {missing.label} is found because of careful listening, not because anyone was bad.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    helper = f["helper"]
    missing = f["missing_cfg"]
    place = f["hide_cfg"]
    cause = f["cause_cfg"]
    actor = f["cause_actor"]
    grownup = f["grownup"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child at the market, and {keeper.id}, who had lost a {missing.label}. It also includes {helper.id}, a market member who helped listen for clues."
        ),
        (
            f"What was missing at the stall?",
            f"The missing thing was the {missing.label}. {keeper.id} needed it to {missing.use}."
        ),
        (
            "What clue did the child hear?",
            f"{hero.id} heard the sound \"{place.clue_sound}. {place.clue_sound}.\" coming from {place.phrase}. That repeating sound made {hero.pronoun('object')} stop and listen instead of guessing too fast."
        ),
        (
            f"How was the mystery solved?",
            f"{hero.id} and {helper.id} followed the sound and checked {place.phrase}. They found the {missing.label} there because the clue led them to the right spot."
        ),
        (
            f"Why was the {missing.label} there?",
            f"It was there because {cause.action_text.replace('{place}', place.label).replace('{item}', missing.label)} That means the item was misplaced by accident, not stolen."
        ),
    ]
    if cause.id == "baby_drop":
        qa.append(
            (
                'How did the word "bub" fit into the story?',
                f'It fit in two ways: the clue sounded like "bub, bub," and the baby who moved the item was named Bub. That repetition helped make the mystery feel playful and memorable.'
            )
        )
    else:
        qa.append(
            (
                "Was anyone mean in the story?",
                f"No. The problem happened by accident, and everyone stayed calm while they solved it. That is why the ending feels gentle even though it begins like a mystery."
            )
        )
    qa.append(
        (
            f"How did {hero.id} feel at the end?",
            f"{hero.id} felt proud and relieved. The market felt bright again once the missing {missing.label} was back in place."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"market", "mystery", "clue"}
    tags |= set(f["missing_cfg"].tags)
    tags |= set(f["hide_cfg"].tags)
    tags |= set(f["cause_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated stories.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        stall="bakery",
        missing="member_badge",
        hiding_place="basket_under_cloth",
        cause="baby_drop",
        helper="porter",
        hero_name="Nora",
        hero_gender="girl",
        grownup="mother",
    ),
    StoryParams(
        stall="fruit",
        missing="coin_pouch",
        hiding_place="crate_gap",
        cause="kitten_nudge",
        helper="guard",
        hero_name="Ben",
        hero_gender="boy",
        grownup="father",
    ),
    StoryParams(
        stall="flower",
        missing="recipe_card",
        hiding_place="paper_stack",
        cause="wind_slide",
        helper="porter",
        hero_name="Mia",
        hero_gender="girl",
        grownup="mother",
    ),
    StoryParams(
        stall="bakery",
        missing="recipe_card",
        hiding_place="basket_under_cloth",
        cause="baby_drop",
        helper="guard",
        hero_name="Leo",
        hero_gender="boy",
        grownup="father",
    ),
]


def explain_rejection(missing_id: str, place_id: str, cause_id: str) -> str:
    missing = MISSING_ITEMS[missing_id]
    place = HIDING_PLACES[place_id]
    cause = CAUSES[cause_id]
    if not item_can_hide_in_place(missing, place):
        return (
            f"(No story: a {missing.label} is not a good fit for {place.label}. "
            f"The hiding place should make sense for the missing item.)"
        )
    if not cause_matches_place(cause, place):
        return (
            f"(No story: {cause.label} does not plausibly put the item at {place.label}. "
            f"Pick a cause and place that fit each other.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(M, P) :- missing(M), place(P), item_fits(M, P).
cause_works(C, P) :- cause(C), place(P), cause_place(C, P).

valid(S, M, P, C) :- stall(S), missing(M), place(P), cause(C), fits(M, P), cause_works(C, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in STALLS:
        lines.append(asp.fact("stall", sid))
    for mid, item in MISSING_ITEMS.items():
        lines.append(asp.fact("missing", mid))
        for pid in sorted(item.fits_places):
            lines.append(asp.fact("item_fits", mid, pid))
    for pid in HIDING_PLACES:
        lines.append(asp.fact("place", pid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for pid in sorted(HIDING_PLACES):
            if cause_matches_place(cause, HIDING_PLACES[pid]):
                lines.append(asp.fact("cause_place", cid, pid))
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("sample missed QA or prompts")
        print("OK: random generation smoke test succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a gentle market mystery with dialogue and repetition."
    )
    ap.add_argument("--stall", choices=STALLS)
    ap.add_argument("--missing", choices=MISSING_ITEMS)
    ap.add_argument("--hiding-place", dest="hiding_place", choices=HIDING_PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.missing and args.hiding_place and args.cause:
        if not valid_combo(args.stall or next(iter(STALLS)), args.missing, args.hiding_place, args.cause):
            raise StoryError(explain_rejection(args.missing, args.hiding_place, args.cause))

    combos = [
        combo for combo in valid_combos()
        if (args.stall is None or combo[0] == args.stall)
        and (args.missing is None or combo[1] == args.missing)
        and (args.hiding_place is None or combo[2] == args.hiding_place)
        and (args.cause is None or combo[3] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    stall_id, missing_id, place_id, cause_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(
        stall=stall_id,
        missing=missing_id,
        hiding_place=place_id,
        cause=cause_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    if params.stall not in STALLS:
        raise StoryError(f"(Unknown stall: {params.stall})")
    if params.missing not in MISSING_ITEMS:
        raise StoryError(f"(Unknown missing item: {params.missing})")
    if params.hiding_place not in HIDING_PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding_place})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not valid_combo(params.stall, params.missing, params.hiding_place, params.cause):
        raise StoryError(explain_rejection(params.missing, params.hiding_place, params.cause))

    world = tell(
        stall=STALLS[params.stall],
        missing=MISSING_ITEMS[params.missing],
        place=HIDING_PLACES[params.hiding_place],
        cause=CAUSES[params.cause],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        grownup_type=params.grownup,
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
        print(f"{len(combos)} compatible (stall, missing, hiding_place, cause) combos:\n")
        for stall_id, missing_id, place_id, cause_id in combos:
            print(f"  {stall_id:8} {missing_id:13} {place_id:18} {cause_id}")
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
            header = (
                f"### {p.hero_name}: {p.missing} at {p.stall} "
                f"({p.hiding_place}, {p.cause})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
