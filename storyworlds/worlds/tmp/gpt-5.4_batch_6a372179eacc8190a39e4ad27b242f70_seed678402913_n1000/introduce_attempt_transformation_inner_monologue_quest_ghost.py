#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/introduce_attempt_transformation_inner_monologue_quest_ghost.py
===========================================================================================

A small ghost-story storyworld about a child who goes on a quest to help a
lonely ghost recover a lost keepsake. The child must choose a gentle approach
that fits the ghost's mood and visit a place where the keepsake could truly be
found. If the combination is reasonable, the story reaches a calm
transformation: the ghost changes from eerie and restless to peaceful and bright.

The seed asked for:
- the words "introduce" and "attempt"
- Transformation
- Inner Monologue
- Quest
- a Ghost Story style

Run it
------
python storyworlds/worlds/gpt-5.4/introduce_attempt_transformation_inner_monologue_quest_ghost.py
python storyworlds/worlds/gpt-5.4/introduce_attempt_transformation_inner_monologue_quest_ghost.py --place lighthouse --ghost sailor --approach humming_song
python storyworlds/worlds/gpt-5.4/introduce_attempt_transformation_inner_monologue_quest_ghost.py --place greenhouse --ghost sailor
python storyworlds/worlds/gpt-5.4/introduce_attempt_transformation_inner_monologue_quest_ghost.py --all
python storyworlds/worlds/gpt-5.4/introduce_attempt_transformation_inner_monologue_quest_ghost.py --qa --json
python storyworlds/worlds/gpt-5.4/introduce_attempt_transformation_inner_monologue_quest_ghost.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
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
class Place:
    id: str
    label: str
    opening: str
    path_text: str
    search_text: str
    ending_text: str
    scariness: int
    hides: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostKind:
    id: str
    label: str
    mood: str
    item: str
    first_seen: str
    request_text: str
    thanks_text: str
    transform_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    hiding_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    label: str
    action_text: str
    inner_text: str
    trust_text: str
    bonus: int
    calms: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Trait:
    id: str
    label: str
    courage: int
    thought_text: str


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


def _r_cold_fear(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    hero = world.entities.get("hero")
    place = world.entities.get("place")
    if not ghost or not hero or not place:
        return []
    if place.meters["cold"] < THRESHOLD:
        return []
    sig = ("cold_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return []


def _r_return_transforms(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    item = world.entities.get("item")
    place = world.entities.get("place")
    hero = world.entities.get("hero")
    if not ghost or not item or not place or not hero:
        return []
    if ghost.memes["trust"] < THRESHOLD or item.meters["returned"] < THRESHOLD:
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["glow"] += 1
    ghost.meters["shadow"] = 0.0
    ghost.memes["peace"] += 1
    place.meters["cold"] = 0.0
    place.meters["warmth"] += 1
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="cold_fear", tag="mood", apply=_r_cold_fear),
    Rule(name="transform", tag="mood", apply=_r_return_transforms),
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
    "attic": Place(
        id="attic",
        label="the attic",
        opening="the attic above her grandmother's hallway",
        path_text="Each stair creaked like a tiny whisper under her slippers.",
        search_text="Moonlight slid across trunks and hatboxes under the sloping roof.",
        ending_text="Even the rafters seemed to stop groaning and listen.",
        scariness=3,
        hides={"ribbon", "music_box", "key"},
        tags={"attic", "old_house"},
    ),
    "lighthouse": Place(
        id="lighthouse",
        label="the old lighthouse",
        opening="the old lighthouse on the windy hill",
        path_text="The round stairs curled upward while the sea boomed far below.",
        search_text="Salt glittered on the windows, and every shelf held something forgotten by the tide.",
        ending_text="The lamp room no longer felt lonely; it felt like a watchful star.",
        scariness=2,
        hides={"compass", "bell", "key"},
        tags={"lighthouse", "sea"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the moonlit greenhouse",
        opening="the moonlit greenhouse behind the garden wall",
        path_text="Wet leaves brushed her sleeves, and the glass panes ticked softly in the wind.",
        search_text="Pots, benches, and curling vines made secret little corners everywhere.",
        ending_text="The panes held silver light instead of shivers.",
        scariness=1,
        hides={"ribbon", "flower", "key"},
        tags={"greenhouse", "garden"},
    ),
    "nursery": Place(
        id="nursery",
        label="the empty nursery",
        opening="the empty nursery at the end of the upstairs hall",
        path_text="A rocking chair moved once, then settled, as if it had remembered a lullaby.",
        search_text="Faded toys waited on shelves, and the wallpaper stars still shone faintly in the dark.",
        ending_text="The nursery felt ready for sleep instead of sadness.",
        scariness=2,
        hides={"music_box", "ribbon"},
        tags={"nursery", "old_house"},
    ),
}

GHOSTS = {
    "sailor": GhostKind(
        id="sailor",
        label="a sailor ghost",
        mood="lonely",
        item="compass",
        first_seen="A pale sailor ghost stood by the window, with coat tails drifting as if underwater.",
        request_text='"I have circled this place so long that I forgot which way home once was," the ghost whispered.',
        thanks_text='"You brought back my way," the ghost said, and the words sounded almost like a laugh.',
        transform_text="The sailor's outline grew clear and pearly, and the torn coat smoothed into quiet silver folds.",
        tags={"ghost", "sea"},
    ),
    "child": GhostKind(
        id="child",
        label="a child ghost",
        mood="shy",
        item="ribbon",
        first_seen="A child ghost peeped from behind a trunk, with one bright eye and a wobble of moon-pale hair.",
        request_text='"I used to wear a blue ribbon," the ghost murmured. "Without it, I never quite feel like myself."',
        thanks_text='"Now I remember my own face," the ghost said softly.',
        transform_text="The little ghost stopped flickering and looked almost like a child standing in a patch of dawn.",
        tags={"ghost", "child"},
    ),
    "caretaker": GhostKind(
        id="caretaker",
        label="a caretaker ghost",
        mood="worried",
        item="key",
        first_seen="A bent caretaker ghost hovered beside a locked cabinet, wringing translucent hands.",
        request_text='"I was meant to keep things safe," the ghost said. "I have worried over one lost key for years."',
        thanks_text='"At last, the house may rest," the ghost sighed.',
        transform_text="The caretaker straightened little by little until the ghost shone like clean glass in lamplight.",
        tags={"ghost", "house"},
    ),
    "ballerina": GhostKind(
        id="ballerina",
        label="a ballerina ghost",
        mood="sad",
        item="music_box",
        first_seen="A ballerina ghost turned in one silent circle, and the hem of her dress shivered like mist.",
        request_text='"My song stopped," the ghost whispered. "Somewhere, my music box is still waiting to be wound."',
        thanks_text='"You found my song again," the ghost said, with tears that looked like tiny stars.',
        transform_text="The ballerina's pale shape filled with gentle color, and her slow turn became graceful instead of mournful.",
        tags={"ghost", "music"},
    ),
}

ITEMS = {
    "compass": Keepsake(
        id="compass",
        label="compass",
        phrase="a brass compass with a cloudy glass face",
        hiding_text="It lay wedged behind an old map case, green with sea salt.",
        tags={"compass", "metal"},
    ),
    "ribbon": Keepsake(
        id="ribbon",
        label="ribbon",
        phrase="a blue ribbon, still silky where the dust had not touched it",
        hiding_text="It had slipped under a cedar chest, where the moon found only one bright edge of blue.",
        tags={"ribbon", "cloth"},
    ),
    "key": Keepsake(
        id="key",
        label="key",
        phrase="a long brass key with a clover-shaped top",
        hiding_text="It had fallen between two cracked flowerpots, almost hidden in the soil.",
        tags={"key", "metal"},
    ),
    "music_box": Keepsake(
        id="music_box",
        label="music box",
        phrase="a little music box painted with faded roses",
        hiding_text="It rested inside a toy cupboard behind a row of wooden blocks, patient and still.",
        tags={"music_box", "music"},
    ),
}

APPROACHES = {
    "soft_hello": Approach(
        id="soft_hello",
        label="a soft hello",
        action_text='She folded her hands and said, "Hello. I came to help, not to chase anyone away."',
        inner_text='I should introduce myself first, she thought. If I sound kind, maybe the ghost will not hide.',
        trust_text="The ghost did not vanish. Instead, the pale face lifted, listening.",
        bonus=0,
        calms={"shy", "worried", "lonely"},
        tags={"hello", "kindness"},
    ),
    "humming_song": Approach(
        id="humming_song",
        label="a humming song",
        action_text="She let a small tune slip into the dark, the sort of tune that keeps your hands steady.",
        inner_text='If my voice shakes, that is all right, she thought. I can still make this brave attempt one note at a time.',
        trust_text="The ghost leaned closer to the sound, as if the tune were a lantern made of breath.",
        bonus=1,
        calms={"sad", "lonely", "shy"},
        tags={"song", "music"},
    ),
    "lantern_glow": Approach(
        id="lantern_glow",
        label="a lantern glow",
        action_text="She lifted her little lantern so the gold circle touched the floor instead of the ghost's face.",
        inner_text='Do not point the light like a weapon, she told herself. Let the room see I mean to help.',
        trust_text="The ghost's tight, worried shape loosened a little in the gentler glow.",
        bonus=1,
        calms={"worried", "shy"},
        tags={"lantern", "light"},
    ),
}

TRAITS = {
    "careful": Trait(
        id="careful",
        label="careful",
        courage=2,
        thought_text="She was careful enough to notice every groan of wood and every patch of colder air.",
    ),
    "brave": Trait(
        id="brave",
        label="brave",
        courage=3,
        thought_text="She was brave in the quiet way, the way that keeps walking even while the knees feel shaky.",
    ),
    "gentle": Trait(
        id="gentle",
        label="gentle",
        courage=2,
        thought_text="She was gentle, and gentleness sometimes reaches places banging never could.",
    ),
    "dreamy": Trait(
        id="dreamy",
        label="dreamy",
        courage=1,
        thought_text="She was dreamy, which meant scary things had to be faced one small thought at a time.",
    ),
}

GIRL_NAMES = ["Mara", "Nina", "Lucy", "Ivy", "Elsie", "Wren", "Clara", "June"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Jasper", "Milo", "Finn", "Rowan", "Noah"]


def valid_combo(place: Place, ghost: GhostKind, approach: Approach) -> bool:
    return ghost.item in place.hides and ghost.mood in approach.calms


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for ghost_id, ghost in GHOSTS.items():
            for approach_id, approach in APPROACHES.items():
                if valid_combo(place, ghost, approach):
                    combos.append((place_id, ghost_id, approach_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    approach = APPROACHES[params.approach]
    trait = TRAITS[params.trait]
    return "steady" if trait.courage + approach.bonus >= place.scariness else "shaky"


def explain_rejection(place: Place, ghost: GhostKind, approach: Approach) -> str:
    reasons: list[str] = []
    if ghost.item not in place.hides:
        reasons.append(
            f"{place.label} is not a believable place to find the ghost's lost {ITEMS[ghost.item].label}"
        )
    if ghost.mood not in approach.calms:
        reasons.append(
            f"{approach.label} would not calm a {ghost.mood} ghost"
        )
    if not reasons:
        reasons.append("this combination does not make a reasonable ghost quest")
    return f"(No story: {'; '.join(reasons)}.)"


@dataclass
class StoryParams:
    place: str
    ghost: str
    approach: str
    name: str
    gender: str
    trait: str
    lantern: bool = True
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="lighthouse",
        ghost="sailor",
        approach="humming_song",
        name="Mara",
        gender="girl",
        trait="brave",
        lantern=True,
    ),
    StoryParams(
        place="nursery",
        ghost="ballerina",
        approach="humming_song",
        name="Theo",
        gender="boy",
        trait="gentle",
        lantern=False,
    ),
    StoryParams(
        place="greenhouse",
        ghost="caretaker",
        approach="soft_hello",
        name="Ivy",
        gender="girl",
        trait="careful",
        lantern=True,
    ),
    StoryParams(
        place="attic",
        ghost="child",
        approach="lantern_glow",
        name="Rowan",
        gender="boy",
        trait="dreamy",
        lantern=True,
    ),
    StoryParams(
        place="attic",
        ghost="ballerina",
        approach="humming_song",
        name="June",
        gender="girl",
        trait="brave",
        lantern=False,
    ),
]


def introduce_scene(world: World, hero: Entity, place: Place, trait: Trait) -> None:
    world.say(
        f"On a silver night, {hero.id} climbed toward {place.opening} because a whispering quest had found {hero.pronoun('object')} first."
    )
    world.say(trait.thought_text)
    world.say(place.path_text)


def first_chill(world: World, hero: Entity, ghost_cfg: GhostKind) -> None:
    place = world.get("place")
    ghost = world.get("ghost")
    place.meters["cold"] += 1
    ghost.meters["shadow"] += 1
    propagate(world, narrate=False)
    world.say(ghost_cfg.first_seen)
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"A cold prickle ran over {hero.pronoun('possessive')} arms, and for a moment {hero.pronoun()} almost turned back."
        )


def inner_monologue(world: World, hero: Entity, approach: Approach, outcome: str) -> None:
    world.say(approach.inner_text)
    if outcome == "shaky":
        world.say(
            f'"My heart is making too much noise," {hero.id} thought, "but quests are still quests even when your shoes want to run the other way."'
        )
    else:
        world.say(
            f'"If I keep my voice steady," {hero.id} thought, "maybe the room will understand I came for something good."'
        )


def introduce_and_attempt(world: World, hero: Entity, approach: Approach, ghost_cfg: GhostKind) -> None:
    world.say(approach.action_text)
    world.say(approach.trust_text)
    ghost = world.get("ghost")
    ghost.memes["trust"] += 1
    hero.memes["courage"] += 1
    world.say(ghost_cfg.request_text)


def search_for_keepsake(world: World, hero: Entity, place: Place, item_cfg: Keepsake, outcome: str) -> None:
    world.say(
        f"{hero.id} looked around. {place.search_text}"
    )
    if outcome == "shaky":
        world.say(
            f"{hero.pronoun().capitalize()} made one timid attempt to open the nearest trunk, then drew back when the lid sighed on its hinges."
        )
        world.say(
            f'"Do it properly," {hero.pronoun()} told {hero.pronoun("object")}self. "The ghost has waited long enough."'
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} made a careful attempt at searching every corner, slow enough not to miss the smallest clue."
        )
    world.say(item_cfg.hiding_text)
    item = world.get("item")
    item.meters["found"] += 1
    hero.memes["hope"] += 1


def return_keepsake(world: World, hero: Entity, ghost_cfg: GhostKind, item_cfg: Keepsake) -> None:
    world.say(
        f'{hero.id} carried {item_cfg.phrase} to the waiting ghost and held it out with both hands.'
    )
    item = world.get("item")
    item.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(ghost_cfg.thanks_text)
    world.say(ghost_cfg.transform_text)


def transformed_ending(world: World, hero: Entity, place: Place, ghost_cfg: GhostKind) -> None:
    ghost = world.get("ghost")
    if ghost.meters["glow"] >= THRESHOLD:
        world.say(
            f"The whole place changed with {ghost.pronoun('object')}: the bitter chill lifted, the shadows softened, and {place.ending_text}"
        )
    world.say(
        f'Before fading upward like a white feather, the ghost bowed and said, "You did not come to steal a story. You came to mend one."'
    )
    world.say(
        f"{hero.id} walked home under the paling moon feeling changed too, because the quest had started with fear and ended with kindness that shone."
    )


def tell(
    place: Place,
    ghost_cfg: GhostKind,
    approach: Approach,
    trait: Trait,
    name: str,
    gender: str,
    lantern: bool,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="hero",
            label=name,
            tags={"child"},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label=ghost_cfg.label,
            tags=set(ghost_cfg.tags),
        )
    )
    place_ent = world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=place.label,
            tags=set(place.tags),
        )
    )
    item_cfg = ITEMS[ghost_cfg.item]
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="keepsake",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            owner="ghost",
            tags=set(item_cfg.tags),
        )
    )
    if lantern:
        world.add(
            Entity(
                id="lantern",
                kind="thing",
                type="tool",
                label="lantern",
                phrase="a little lantern",
                tags={"light"},
            )
        )

    introduce_scene(world, hero, place, trait)
    world.para()
    first_chill(world, hero, ghost_cfg)
    inner_monologue(world, hero, approach, outcome_of(StoryParams(
        place=place.id,
        ghost=ghost_cfg.id,
        approach=approach.id,
        name=name,
        gender=gender,
        trait=trait.id,
        lantern=lantern,
    )))
    introduce_and_attempt(world, hero, approach, ghost_cfg)
    world.para()
    search_for_keepsake(world, hero, place, item_cfg, outcome_of(StoryParams(
        place=place.id,
        ghost=ghost_cfg.id,
        approach=approach.id,
        name=name,
        gender=gender,
        trait=trait.id,
        lantern=lantern,
    )))
    return_keepsake(world, hero, ghost_cfg, item_cfg)
    world.para()
    transformed_ending(world, hero, place, ghost_cfg)

    world.facts.update(
        hero=hero,
        ghost=ghost,
        ghost_cfg=ghost_cfg,
        place=place,
        item=item,
        item_cfg=item_cfg,
        approach=approach,
        trait=trait,
        lantern=lantern,
        outcome=outcome_of(StoryParams(
            place=place.id,
            ghost=ghost_cfg.id,
            approach=approach.id,
            name=name,
            gender=gender,
            trait=trait.id,
            lantern=lantern,
        )),
        transformed=ghost.meters["glow"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a tale about a spirit or a haunting. It often feels spooky, but it can also be gentle and sad.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a clear purpose. Someone goes looking for something important and keeps going even when it feels hard.",
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass helps you know direction. Its needle points north, which can help travelers find their way.",
        )
    ],
    "ribbon": [
        (
            "Why can a ribbon matter in a story?",
            "A ribbon can be small but still important. If it belongs to someone special, it can hold strong memories.",
        )
    ],
    "key": [
        (
            "What is a key for?",
            "A key opens a lock. In stories, it can also mean safety, secrets, or something that has been shut away.",
        )
    ],
    "music_box": [
        (
            "What is a music box?",
            "A music box is a little box that plays a tune when it is wound. Its song can make people remember things.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes a steady light so you can see in the dark. In stories, it often stands for guidance and courage.",
        )
    ],
    "song": [
        (
            "Why can humming calm someone down?",
            "A soft tune is slow and gentle, so it can help a frightened or lonely person feel less alone. Music can make a place feel safer.",
        )
    ],
    "kindness": [
        (
            "Why is kindness useful when someone is scared?",
            "Kindness shows that you mean no harm. A calm voice and gentle words can help fear loosen its grip.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "quest", "compass", "ribbon", "key", "music_box", "lantern", "song", "kindness"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    ghost_cfg = world.facts["ghost_cfg"]
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "introduce" and "attempt".',
        f"Tell a story about a {hero.type} named {hero.id} who goes on a quest through {place.label} to help {ghost_cfg.label} find a lost {item_cfg.label}.",
        "Write a spooky-but-safe story with inner monologue, a searching quest, and a transformation from haunting sadness to peace.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    ghost_cfg = world.facts["ghost_cfg"]
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    approach = world.facts["approach"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who goes into {place.label}, and {ghost_cfg.label} who has lost a treasured {item_cfg.label}. The story follows their meeting and the quest that joins them.",
        ),
        (
            f"Why did {hero.id} go into {place.label}?",
            f"{hero.id} went because the place felt haunted and in need of help. The quest was to find the ghost's missing {item_cfg.label} and bring peace back to the room.",
        ),
        (
            f"What did {hero.id} do before speaking to the ghost?",
            f"{hero.id} stopped to think first and had an inner monologue about being afraid. Then {hero.pronoun().capitalize()} chose {approach.label} so the ghost would know {hero.pronoun()} came kindly.",
        ),
        (
            f"What was {hero.id}'s first attempt like?",
            f"The first attempt was gentle instead of noisy. That mattered because the ghost was {ghost_cfg.mood}, so a softer approach gave it a reason to trust {hero.pronoun('object')}.",
        ),
        (
            f"What did {hero.id} find on the quest?",
            f"{hero.pronoun().capitalize()} found {item_cfg.phrase}. Finding the right keepsake changed the story, because the ghost had been waiting for that one missing thing.",
        ),
    ]
    if world.facts["transformed"]:
        extra = "At first the child had to gather courage again before searching properly." if outcome == "shaky" else "The child's steady courage helped the search move forward."
        qa.append(
            (
                "How did the ghost transform at the end?",
                f"The ghost changed from eerie and restless to peaceful and bright after receiving the lost {item_cfg.label}. {extra}",
            )
        )
        qa.append(
            (
                "How did the place change at the end?",
                f"The place stopped feeling bitterly cold and haunted. Its shadows softened because the ghost's worry had been healed.",
            )
        )
        qa.append(
            (
                f"How did {hero.id} change?",
                f"{hero.id} began the story frightened, but ended feeling brave in a deeper way. The quest taught {hero.pronoun('object')} that kindness can be stronger than fear.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "quest"} | set(world.facts["item_cfg"].tags) | set(world.facts["approach"].tags)
    if world.facts.get("lantern"):
        tags.add("lantern")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        parts: list[str] = [f"({ent.type})"]
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, G, A) :- setting(P), ghost(G), approach(A),
                  needs(G, I), hides(P, I),
                  mood(G, M), calms(A, M).

score(S) :- chosen_place(P), scariness(P, Sc),
            chosen_trait(T), courage(T, C),
            chosen_approach(A), bonus(A, B),
            S = C + B - Sc.

outcome(steady) :- score(S), S >= 0.
outcome(shaky)  :- score(S), S < 0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("setting", place_id))
        lines.append(asp.fact("scariness", place_id, place.scariness))
        for item in sorted(place.hides):
            lines.append(asp.fact("hides", place_id, item))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        lines.append(asp.fact("needs", ghost_id, ghost.item))
        lines.append(asp.fact("mood", ghost_id, ghost.mood))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("bonus", approach_id, approach.bonus))
        for mood in sorted(approach.calms):
            lines.append(asp.fact("calms", approach_id, mood))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("courage", trait_id, trait.courage))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_approach", params.approach),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        a = asp_outcome(params)
        p = outcome_of(params)
        if a != p:
            rc = 1
            print(f"MISMATCH in outcome for {params}: clingo={a} python={p}")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="smoke")
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    if rc == 0:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child goes on a ghostly quest to help a lonely spirit."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--no-lantern", action="store_true", help="tell the story without a lantern prop")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def explain_missing(place_id: Optional[str], ghost_id: Optional[str], approach_id: Optional[str]) -> str:
    parts = []
    if place_id and place_id not in PLACES:
        parts.append(f"unknown place '{place_id}'")
    if ghost_id and ghost_id not in GHOSTS:
        parts.append(f"unknown ghost '{ghost_id}'")
    if approach_id and approach_id not in APPROACHES:
        parts.append(f"unknown approach '{approach_id}'")
    return ", ".join(parts)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError(explain_missing(args.place, None, None))
    if args.ghost and args.ghost not in GHOSTS:
        raise StoryError(explain_missing(None, args.ghost, None))
    if args.approach and args.approach not in APPROACHES:
        raise StoryError(explain_missing(None, None, args.approach))
    if args.place and args.ghost and args.approach:
        place = PLACES[args.place]
        ghost = GHOSTS[args.ghost]
        approach = APPROACHES[args.approach]
        if not valid_combo(place, ghost, approach):
            raise StoryError(explain_rejection(place, ghost, approach))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.approach is None or combo[2] == args.approach)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, ghost_id, approach_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        place=place_id,
        ghost=ghost_id,
        approach=approach_id,
        name=name,
        gender=gender,
        trait=trait,
        lantern=not args.no_lantern,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.ghost not in GHOSTS:
        raise StoryError(f"(No story: unknown ghost '{params.ghost}'.)")
    if params.approach not in APPROACHES:
        raise StoryError(f"(No story: unknown approach '{params.approach}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(No story: unknown trait '{params.trait}'.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown gender '{params.gender}'.)")
    place = PLACES[params.place]
    ghost = GHOSTS[params.ghost]
    approach = APPROACHES[params.approach]
    trait = TRAITS[params.trait]
    if not valid_combo(place, ghost, approach):
        raise StoryError(explain_rejection(place, ghost, approach))

    world = tell(
        place=place,
        ghost_cfg=ghost,
        approach=approach,
        trait=trait,
        name=params.name,
        gender=params.gender,
        lantern=params.lantern,
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
        print(f"{len(combos)} compatible (place, ghost, approach) combos:\n")
        for place_id, ghost_id, approach_id in combos:
            print(f"  {place_id:10} {ghost_id:10} {approach_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.ghost} in {p.place} with {p.approach} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
