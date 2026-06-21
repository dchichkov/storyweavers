#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/collection_rhyme_heartwarming.py
===========================================================

A small storyworld about a child building a treasured collection. The stories
are heartwarming and use little rhymes inside the action, but the plot is still
driven by simulated state: a growing collection, an unsafe way to carry it, a
warning, a turn, and a warmer ending that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/collection_rhyme_heartwarming.py
    python storyworlds/worlds/gpt-5.4/collection_rhyme_heartwarming.py --place beach --collectible shells
    python storyworlds/worlds/gpt-5.4/collection_rhyme_heartwarming.py --collectible leaves --place beach
    python storyworlds/worlds/gpt-5.4/collection_rhyme_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/collection_rhyme_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/collection_rhyme_heartwarming.py --verify
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
POCKET_CAPACITY = 3
CAREFUL_TRAITS = {"careful", "gentle", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    intro: str
    ground: str
    breeze: str
    recoverable: bool = True
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Collectible:
    id: str
    label: str
    one: str
    plural: bool = True
    material: str = "sturdy"
    found_text: str = ""
    gleam: str = ""
    rhyme_call: str = ""
    rhyme_answer: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Keeper:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    carry_bonus: int = 3
    use_text: str = ""
    ending_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_overflow(world: World) -> list[str]:
    child = world.get("child")
    pile = world.get("collection")
    if pile.meters["count"] <= child.attrs.get("carry_capacity", POCKET_CAPACITY):
        return []
    if ("overflow",) in world.fired:
        return []
    world.fired.add(("overflow",))
    pile.meters["spill_risk"] += 1
    child.memes["worry"] += 1
    return []


def _r_fragile(world: World) -> list[str]:
    child = world.get("child")
    pile = world.get("collection")
    cfg = world.facts["collectible_cfg"]
    if cfg.material != "fragile":
        return []
    if child.attrs.get("carrier") != "pocket":
        return []
    if ("fragile",) in world.fired:
        return []
    world.fired.add(("fragile",))
    pile.meters["bend_risk"] += 1
    child.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="overflow", tag="physical", apply=_r_overflow),
    Rule(name="fragile", tag="physical", apply=_r_fragile),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = changed or False
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


def collectible_allowed(place: Place, collectible: Collectible) -> bool:
    return collectible.id in place.affords


def keeper_works(collectible: Collectible, keeper: Keeper) -> bool:
    return collectible.material in keeper.protects


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for collectible_id, collectible in COLLECTIBLES.items():
            if not collectible_allowed(place, collectible):
                continue
            for keeper_id, keeper in KEEPERS.items():
                if keeper_works(collectible, keeper):
                    out.append((place_id, collectible_id, keeper_id))
    return out


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_listen(relation: str, child_age: int, helper_age: int, helper_trait: str) -> bool:
    older = relation in {"siblings", "cousins"} and helper_age > child_age
    authority = initial_care(helper_trait) + (3.0 if older else 0.0)
    return older and authority >= 7.0


def outcome_of(params: "StoryParams") -> str:
    if would_listen(
        relation=params.relation,
        child_age=params.child_age,
        helper_age=params.helper_age,
        helper_trait=params.helper_trait,
    ):
        return "tidy"
    if PLACES[params.place].recoverable:
        return "rescued"
    return "smaller"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    pile = sim.get("collection")
    cfg = sim.facts["collectible_cfg"]
    pile.meters["count"] += 2
    child.attrs["carrier"] = "pocket"
    child.attrs["carry_capacity"] = POCKET_CAPACITY
    propagate(sim, narrate=False)
    return {
        "overflow": pile.meters["spill_risk"] >= THRESHOLD,
        "bend": pile.meters["bend_risk"] >= THRESHOLD,
        "count": int(pile.meters["count"]),
        "recoverable": sim.place.recoverable,
        "material": cfg.material,
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"One soft afternoon, {child.id} and {helper.id} walked through {place.label}. "
        f"{place.intro}"
    )
    world.say(
        f"{child.id} loved noticing small treasures, and soon {child.pronoun()} began a little collection."
    )


def find_first(world: World, child: Entity, collectible: Collectible, place: Place) -> None:
    pile = world.get("collection")
    pile.meters["count"] = 3
    child.memes["joy"] += 1
    world.say(
        f"{collectible.found_text} In the middle of {place.ground}, {child.id} found "
        f"three {collectible.label} that {collectible.gleam}."
    )
    world.say(
        f'"{collectible.rhyme_call}," {child.id} sang. "{collectible.rhyme_answer}."'
    )
    world.say(
        f"{child.pronoun().capitalize()} tucked the little collection into {child.pronoun('possessive')} pocket and patted it proudly."
    )


def want_more(world: World, child: Entity, collectible: Collectible) -> None:
    pile = world.get("collection")
    pile.meters["count"] += 2
    child.memes["greed_for_more"] += 1
    world.say(
        f"But then {child.id} spotted two more {collectible.label}. They were too lovely to leave behind, so "
        f"{child.pronoun()} slipped those in too."
    )


def warn(world: World, helper: Entity, child: Entity, collectible: Collectible, keeper: Keeper) -> None:
    prediction = predict_trouble(world)
    world.facts["predicted_overflow"] = prediction["overflow"]
    world.facts["predicted_bend"] = prediction["bend"]
    helper.memes["care"] += 1
    lines: list[str] = []
    if prediction["bend"]:
        lines.append(f"the pocket might crumple the {collectible.label}")
    if prediction["overflow"]:
        lines.append(f"the pocket was already too full")
    reason = " and ".join(lines) if lines else "pockets are not the best place for a tiny treasure"
    world.say(
        f'{helper.id} touched the bulging pocket and said, "Slow and low, don\'t let them go. '
        f'Let\'s use {keeper.phrase}, because {reason}."'
    )


def agree(world: World, child: Entity, helper: Entity, keeper: Keeper) -> None:
    child.memes["trust"] += 1
    helper.memes["relief"] += 1
    child.attrs["carrier"] = keeper.id
    child.attrs["carry_capacity"] = POCKET_CAPACITY + keeper.carry_bonus
    world.say(
        f"{child.id} stopped, listened, and nodded. Together they used {keeper.phrase}, and at once the little collection sat safer."
    )
    world.say(
        f'"Safe inside, side by side," {helper.id} said, and {child.id} smiled at the rhyme.'
    )


def ignore_warning(world: World, child: Entity, helper: Entity) -> None:
    child.memes["stubborn"] += 1
    world.say(
        f'But {child.id} was still glowing with the fun of finding things. "{child.pronoun("subject").capitalize()} can hold," '
        f"{helper.id} heard {child.pronoun('object')} insist, and off {child.pronoun()} skipped with the pocket still stuffed."
    )


def spill(world: World, child: Entity, collectible: Collectible, place: Place) -> None:
    pile = world.get("collection")
    lost = 2 if not place.recoverable else 0
    spilled = 2
    pile.meters["spilled"] += spilled
    pile.meters["count"] = max(1.0, pile.meters["count"] - lost)
    if collectible.material == "fragile":
        pile.meters["bent"] += 1
    child.memes["sadness"] += 1
    world.say(
        f"Then the pocket gave a small tug and a sudden tip. Out tumbled the {collectible.label}, skipping and scattering across {place.ground}."
    )
    if collectible.material == "fragile":
        world.say(
            f"One {collectible.one} bent at the edge, and {child.id}'s face fell."
        )
    if place.recoverable:
        world.say(
            f"The treasures had not gone far, but they were no longer neat or safe."
        )
    else:
        world.say(
            f"A quick gust and the moving edge of the place carried some away before little hands could catch them."
        )


def rescue(world: World, child: Entity, helper: Entity, keeper: Keeper, collectible: Collectible, place: Place) -> None:
    pile = world.get("collection")
    child.attrs["carrier"] = keeper.id
    child.attrs["carry_capacity"] = POCKET_CAPACITY + keeper.carry_bonus
    child.memes["relief"] += 1
    helper.memes["care"] += 1
    if place.recoverable:
        world.say(
            f"{helper.id} knelt at once. {keeper.use_text.capitalize()}, the two of them gathered each {collectible.one} with careful fingers."
        )
        world.say(
            f'"Find and mind, be soft and kind," {helper.id} whispered, and {child.id} whispered it back.'
        )
    else:
        world.say(
            f"{helper.id} hurried close and held out {keeper.phrase}. They could not save every single one, but they tucked the ones they could reach into the safe keeper."
        )
        world.say(
            f'"Not the most, but still the best, when love can hold the ones that rest," {helper.id} said softly.'
        )


def ending_tidy(world: World, child: Entity, helper: Entity, keeper: Keeper, collectible: Collectible) -> None:
    pile = world.get("collection")
    child.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By the time the sun leaned lower, their collection had grown to {int(pile.meters['count'])} {collectible.label}, all resting in {keeper.phrase}."
    )
    world.say(
        f"At home they made a small display by the window, and every little treasure looked brighter because they had cared for it together."
    )
    world.say(
        f'{keeper.ending_text} "{collectible.rhyme_call}, safe tonight," {child.id} said. "{collectible.rhyme_answer}," {helper.id} answered.'
    )


def ending_rescued(world: World, child: Entity, helper: Entity, keeper: Keeper, collectible: Collectible) -> None:
    pile = world.get("collection")
    child.memes["pride"] += 1
    child.memes["love"] += 1
    world.say(
        f"After that, {child.id} carried the collection in {keeper.phrase} and walked much more gently. What had almost been lost now felt even more special."
    )
    world.say(
        f"That evening they sorted the {collectible.label} on a warm table, and each one seemed to say that being careful could be part of the fun."
    )
    world.say(
        f'"Side by side, safe inside," they sang together, and the room felt full of quiet pride.'
    )
    if pile.meters["bent"] >= THRESHOLD:
        world.say(
            f"Even the bent little {collectible.one} was kept, because {helper.id} said loved things do not have to be perfect to belong."
        )


def ending_smaller(world: World, child: Entity, helper: Entity, keeper: Keeper, collectible: Collectible) -> None:
    pile = world.get("collection")
    child.memes["acceptance"] += 1
    helper.memes["love"] += 1
    world.say(
        f"When they finally sat down together, the collection was smaller than before, but the saved {collectible.label} rested snugly in {keeper.phrase}."
    )
    world.say(
        f"{helper.id} helped {child.id} choose one favorite {collectible.one} for the very middle, and somehow that made the whole little group feel complete."
    )
    world.say(
        f'"Less can bless," {helper.id} murmured, and {child.id} leaned close, smiling at the sound of it.'
    )
    world.say(
        f"From then on, the collection was not just about finding things. It was about who had knelt down together to protect them."
    )


def tell(
    place: Place,
    collectible: Collectible,
    keeper: Keeper,
    *,
    child_name: str = "Lily",
    child_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    helper_trait: str = "careful",
    relation: str = "siblings",
    child_age: int = 5,
    helper_age: int = 7,
    elder_type: str = "grandmother",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            age=child_age,
            traits=["curious"],
            attrs={"carrier": "pocket", "carry_capacity": POCKET_CAPACITY, "relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            age=helper_age,
            traits=[helper_trait],
            attrs={"relation": relation},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    pile = world.add(
        Entity(
            id="collection",
            type="collection",
            label=f"{collectible.label} collection",
        )
    )
    keep = world.add(
        Entity(
            id=keeper.id,
            type="keeper",
            label=keeper.label,
            phrase=keeper.phrase,
            tags=set(keeper.tags),
        )
    )

    world.facts.update(
        child=child,
        helper=helper,
        elder=elder,
        collection=pile,
        keeper=keep,
        place_cfg=place,
        collectible_cfg=collectible,
        keeper_cfg=keeper,
        relation=relation,
    )

    introduce(world, child, helper, place)
    find_first(world, child, collectible, place)

    world.para()
    want_more(world, child, collectible)
    propagate(world, narrate=False)
    warn(world, helper, child, collectible, keeper)

    listened = would_listen(
        relation=relation,
        child_age=child_age,
        helper_age=helper_age,
        helper_trait=helper_trait,
    )

    world.para()
    if listened:
        agree(world, child, helper, keeper)
        world.para()
        world.say(
            f"When they reached home, {elder.label_word.capitalize()} cleared a little shelf just for the collection and said there was room for anything gathered with care."
        )
        ending_tidy(world, child, helper, keeper, collectible)
        outcome = "tidy"
    else:
        ignore_warning(world, child, helper)
        spill(world, child, collectible, place)
        world.para()
        rescue(world, child, helper, keeper, collectible, place)
        world.say(
            f"When they reached home, {elder.label_word.capitalize()} brought out a clean cloth and made space on the table for the rescued collection."
        )
        world.para()
        if place.recoverable:
            ending_rescued(world, child, helper, keeper, collectible)
            outcome = "rescued"
        else:
            ending_smaller(world, child, helper, keeper, collectible)
            outcome = "smaller"

    world.facts.update(
        listened=listened,
        outcome=outcome,
        final_count=int(world.get("collection").meters["count"]),
        spilled=world.get("collection").meters["spilled"] >= THRESHOLD,
        bent=world.get("collection").meters["bent"] >= THRESHOLD,
    )
    return world


PLACES = {
    "beach": Place(
        id="beach",
        label="the beach",
        intro="The water kept folding shiny lines onto the sand.",
        ground="the damp sand",
        breeze="a sea breeze",
        recoverable=False,
        affords={"shells", "pebbles"},
        tags={"beach", "wind"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        intro="The flower beds smelled sweet, and the path had little pockets of shade.",
        ground="the soft grass",
        breeze="a light garden breeze",
        recoverable=True,
        affords={"leaves", "pebbles"},
        tags={"garden", "leaves"},
    ),
    "park": Place(
        id="park",
        label="the park",
        intro="A long path curved under trees, and the benches were warm from the day.",
        ground="the path by the trees",
        breeze="a playful breeze",
        recoverable=True,
        affords={"leaves", "acorns"},
        tags={"park", "trees"},
    ),
}

COLLECTIBLES = {
    "shells": Collectible(
        id="shells",
        label="shells",
        one="shell",
        plural=True,
        material="sturdy",
        found_text="Near the edge of the water, tiny ridges winked in the light.",
        gleam="shone pink and cream",
        rhyme_call="Shells to keep",
        rhyme_answer="A shining heap",
        tags={"shells", "collection"},
    ),
    "pebbles": Collectible(
        id="pebbles",
        label="pebbles",
        one="pebble",
        plural=True,
        material="sturdy",
        found_text="Beside the path, smooth little stones waited like quiet marbles.",
        gleam="glowed gray and blue",
        rhyme_call="Pebbles small",
        rhyme_answer="I love them all",
        tags={"pebbles", "collection"},
    ),
    "leaves": Collectible(
        id="leaves",
        label="leaves",
        one="leaf",
        plural=True,
        material="fragile",
        found_text="Under the branches, bright shapes rested where the light could reach them.",
        gleam="glowed gold and red",
        rhyme_call="Leaf so light",
        rhyme_answer="Keep you bright",
        tags={"leaves", "collection"},
    ),
    "acorns": Collectible(
        id="acorns",
        label="acorns",
        one="acorn",
        plural=True,
        material="sturdy",
        found_text="Near the roots, little brown caps peeped out from the earth.",
        gleam="looked neat and round",
        rhyme_call="Acorn round",
        rhyme_answer="Treasure found",
        tags={"acorns", "collection"},
    ),
}

KEEPERS = {
    "jar": Keeper(
        id="jar",
        label="jar",
        phrase="a little glass jar",
        protects={"sturdy"},
        carry_bonus=4,
        use_text="with the jar open between them",
        ending_text="The jar caught the late light and made the collection glow",
        tags={"jar", "container"},
    ),
    "tin": Keeper(
        id="tin",
        label="tin",
        phrase="a small tin with a lid",
        protects={"sturdy"},
        carry_bonus=5,
        use_text="with the tin open between them",
        ending_text="The tin clicked shut with a tiny happy sound",
        tags={"tin", "container"},
    ),
    "press_book": Keeper(
        id="press_book",
        label="press book",
        phrase="a flat press book",
        protects={"fragile"},
        carry_bonus=5,
        use_text="with the press book ready on the ground",
        ending_text="The press book lay on the shelf like a small secret garden",
        tags={"book", "container"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli", "Theo"]
HELPER_TRAITS = ["careful", "gentle", "steady", "thoughtful", "cheerful", "curious"]
RELATIONS = ["siblings", "cousins", "friends"]
ELDERS = ["grandmother", "grandfather", "mother", "father"]


@dataclass
class StoryParams:
    place: str
    collectible: str
    keeper: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_trait: str
    relation: str
    child_age: int = 5
    helper_age: int = 7
    elder_type: str = "grandmother"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="park",
        collectible="leaves",
        keeper="press_book",
        child_name="Lily",
        child_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        helper_trait="careful",
        relation="siblings",
        child_age=5,
        helper_age=8,
        elder_type="grandmother",
    ),
    StoryParams(
        place="garden",
        collectible="pebbles",
        keeper="jar",
        child_name="Max",
        child_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        helper_trait="thoughtful",
        relation="friends",
        child_age=6,
        helper_age=6,
        elder_type="grandfather",
    ),
    StoryParams(
        place="beach",
        collectible="shells",
        keeper="tin",
        child_name="Ava",
        child_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        helper_trait="gentle",
        relation="cousins",
        child_age=5,
        helper_age=7,
        elder_type="mother",
    ),
    StoryParams(
        place="park",
        collectible="acorns",
        keeper="tin",
        child_name="Eli",
        child_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        helper_trait="cheerful",
        relation="friends",
        child_age=6,
        helper_age=6,
        elder_type="father",
    ),
]


KNOWLEDGE = {
    "collection": [
        (
            "What is a collection?",
            "A collection is a group of things someone gathers and keeps together because they are interesting or special."
        )
    ],
    "shells": [
        (
            "What are shells?",
            "Shells are the hard outer homes that once protected little sea animals. People often find empty shells on the beach."
        )
    ],
    "pebbles": [
        (
            "What is a pebble?",
            "A pebble is a small smooth stone. Water and wind can rub stones until they become round and soft to touch."
        )
    ],
    "leaves": [
        (
            "Why can leaves tear or bend easily?",
            "Leaves are thin and light, so they can crumple or rip if they are squeezed into a pocket."
        )
    ],
    "acorns": [
        (
            "What is an acorn?",
            "An acorn is the seed of an oak tree. Squirrels and other animals often collect them for food."
        )
    ],
    "jar": [
        (
            "Why is a jar good for holding little treasures?",
            "A jar keeps small things together in one place, so they are less likely to fall out or get lost."
        )
    ],
    "tin": [
        (
            "Why is a tin with a lid useful?",
            "A tin with a lid helps keep tiny objects together and protected when you carry them around."
        )
    ],
    "book": [
        (
            "What does a press book do for leaves?",
            "A press book holds leaves flat so they do not crumple as easily. It helps fragile things stay neat."
        )
    ],
    "wind": [
        (
            "Why can wind make little objects hard to keep?",
            "Wind can push light things along the ground or into the air. That makes tiny treasures easier to lose."
        )
    ],
}
KNOWLEDGE_ORDER = ["collection", "shells", "pebbles", "leaves", "acorns", "jar", "tin", "book", "wind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    collectible = f["collectible_cfg"]
    keeper = f["keeper_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a heartwarming story for a 3-to-5-year-old about a child making a collection of {collectible.label}. '
        f'Include at least one gentle rhyme.'
    )
    if outcome == "tidy":
        return [
            base,
            f"Tell a story where {child.id} wants to keep adding to a little collection, listens to {helper.id}'s careful warning, and uses {keeper.phrase} before anything spills.",
            f'Write a sweet rhyming story that includes the word "collection" and ends with the treasures displayed safely at home.',
        ]
    if outcome == "rescued":
        return [
            base,
            f"Tell a story where {child.id} ignores a warning, spills the collection, and then {helper.id} helps gather everything into {keeper.phrase}.",
            f'Write a heartwarming rhyme-filled story where a messy middle becomes a lesson about caring for small things together.',
        ]
    return [
        base,
        f"Tell a story where part of the collection blows away, but {child.id} and {helper.id} save the rest and make the smaller collection feel special.",
        f'Write a gentle story with rhyme where losing some treasures leads to a warmer, more loving ending.',
    ]


def pair_noun(child: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if child.type == "girl" and helper.type == "girl":
            return "two sisters"
        if child.type == "boy" and helper.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    if relation == "cousins":
        return "two cousins"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    collectible = f["collectible_cfg"]
    keeper = f["keeper_cfg"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(child, helper, relation)}, {child.id} and {helper.id}. They spend the day making a little collection together."
        ),
        (
            f"What was {child.id} collecting?",
            f"{child.id} was collecting {collectible.label}. The little treasures felt special because each one had its own color and shape."
        ),
        (
            f"Why did {helper.id} worry about the pocket?",
            (
                f"{helper.id} worried because the pocket was getting too full"
                + (" and could bend the fragile pieces." if f.get("predicted_bend") else ".")
                + " The warning came before the trouble, because the collection had grown beyond a safe way to carry it."
            ),
        ),
    ]
    if f["outcome"] == "tidy":
        qa.append(
            (
                f"What changed after {child.id} listened?",
                f"{child.id} moved the collection into {keeper.phrase}, so nothing spilled and everything stayed neat. Listening turned the problem into a cozy ending instead of an accident."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the collection safe at home on a little display. The ending image shows that careful choices helped the treasures last."
            )
        )
    elif f["outcome"] == "rescued":
        qa.append(
            (
                f"What happened when {child.id} did not listen right away?",
                f"The collection spilled out and scattered, which made {child.id} feel upset. Then {helper.id} helped gather the pieces into {keeper.phrase}, so the problem became a lesson in being gentle."
            )
        )
        qa.append(
            (
                "How did they fix the problem?",
                f"They picked up the fallen {collectible.label} together and started carrying them in {keeper.phrase}. Working together mattered because the safer keeper stopped the trouble from happening again."
            )
        )
    else:
        qa.append(
            (
                "Did they save every treasure?",
                f"No. Some of the collection got away, but they saved the rest and treated it with extra care. The smaller collection still felt important because it was protected with love."
            )
        )
        qa.append(
            (
                "Why was the ending still heartwarming?",
                f"The ending stayed warm because {helper.id} helped {child.id} care for what remained instead of scolding. Their smaller collection became a sign of closeness, not just of loss."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"collection"} | set(world.facts["collectible_cfg"].tags) | set(world.place.tags)
    tags |= set(world.facts["keeper_cfg"].tags)
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
        parts: list[str] = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.age:
            parts.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, collectible: Collectible, keeper: Optional[Keeper] = None) -> str:
    if not collectible_allowed(place, collectible):
        return (
            f"(No story: {collectible.label.capitalize()} do not belong naturally in {place.label} here, "
            f"so the collection would feel ungrounded. Pick a place that really offers them.)"
        )
    if keeper is not None and not keeper_works(collectible, keeper):
        return (
            f"(No story: {keeper.phrase.capitalize()} is not a sensible keeper for {collectible.label}. "
            f"The keeper should protect something {collectible.material}, not make the problem weaker.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
collectible_allowed(P, C) :- place(P), collectible(C), found_at(P, C).
keeper_works(C, K) :- collectible(C), keeper(K), material(C, M), protects(K, M).
valid(P, C, K) :- collectible_allowed(P, C), keeper_works(C, K).

care_init(5) :- helper_trait(T), careful_trait(T).
care_init(3) :- helper_trait(T), not careful_trait(T).
older_helper :- relation(siblings), helper_age(HA), child_age(CA), HA > CA.
older_helper :- relation(cousins), helper_age(HA), child_age(CA), HA > CA.
bonus(3) :- older_helper.
bonus(0) :- not older_helper.
authority(C + B) :- care_init(C), bonus(B).
listens :- older_helper, authority(A), A >= 7.

outcome(tidy) :- listens.
outcome(rescued) :- not listens, recoverable.
outcome(smaller) :- not listens, not recoverable.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.recoverable:
            lines.append(asp.fact("recoverable_place", place_id))
        for collectible_id in sorted(place.affords):
            lines.append(asp.fact("found_at", place_id, collectible_id))
    for collectible_id, collectible in COLLECTIBLES.items():
        lines.append(asp.fact("collectible", collectible_id))
        lines.append(asp.fact("material", collectible_id, collectible.material))
    for keeper_id, keeper in KEEPERS.items():
        lines.append(asp.fact("keeper", keeper_id))
        for material in sorted(keeper.protects):
            lines.append(asp.fact("protects", keeper_id, material))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"""
{asp_facts()}
{ASP_RULES}
recoverable :- chosen_place(P), recoverable_place(P).
{extra}
{show}
""".strip() + "\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("helper_trait", params.helper_trait),
            asp.fact("relation", params.relation),
            asp.fact("child_age", params.child_age),
            asp.fact("helper_age", params.helper_age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or not sample.story.strip():
        raise StoryError("(Smoke test failed: generated empty story.)")
    emit(sample, trace=False, qa=False)


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

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a heartwarming little collection, a warning, and a safer way to keep tiny treasures."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--collectible", choices=COLLECTIBLES)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.collectible:
        place = PLACES[args.place]
        collectible = COLLECTIBLES[args.collectible]
        if not collectible_allowed(place, collectible):
            raise StoryError(explain_rejection(place, collectible))
    if args.collectible and args.keeper:
        collectible = COLLECTIBLES[args.collectible]
        keeper = KEEPERS[args.keeper]
        if not keeper_works(collectible, keeper):
            place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
            raise StoryError(explain_rejection(place, collectible, keeper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.collectible is None or combo[1] == args.collectible)
        and (args.keeper is None or combo[2] == args.keeper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, collectible_id, keeper_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=child_name)
    helper_trait = rng.choice(HELPER_TRAITS)
    relation = args.relation or rng.choice(RELATIONS)
    child_age, helper_age = rng.sample([4, 5, 6, 7, 8], 2)
    elder = args.elder or rng.choice(ELDERS)

    return StoryParams(
        place=place_id,
        collectible=collectible_id,
        keeper=keeper_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        relation=relation,
        child_age=child_age,
        helper_age=helper_age,
        elder_type=elder,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        collectible = COLLECTIBLES[params.collectible]
        keeper = KEEPERS[params.keeper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not collectible_allowed(place, collectible):
        raise StoryError(explain_rejection(place, collectible))
    if not keeper_works(collectible, keeper):
        raise StoryError(explain_rejection(place, collectible, keeper))

    world = tell(
        place=place,
        collectible=collectible,
        keeper=keeper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        relation=params.relation,
        child_age=params.child_age,
        helper_age=params.helper_age,
        elder_type=params.elder_type,
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
        print(f"{len(combos)} compatible (place, collectible, keeper) combos:\n")
        for place_id, collectible_id, keeper_id in combos:
            print(f"  {place_id:8} {collectible_id:11} {keeper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} & {p.helper_name}: {p.collectible} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
