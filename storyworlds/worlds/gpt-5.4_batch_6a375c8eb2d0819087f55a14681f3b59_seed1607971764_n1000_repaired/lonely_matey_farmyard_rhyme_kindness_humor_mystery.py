#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lonely_matey_farmyard_rhyme_kindness_humor_mystery.py
================================================================================

A standalone story world about a lonely farmyard animal, a playful little
mystery, and a kind ending. The world is built around one clear premise:

    A lonely animal in the farmyard hears a strange sound and finds rhyming
    clues. The clues feel mysterious and a little funny. At the end, a kind
    friend is revealed: someone planned the clue trail to invite the lonely
    animal into company.

The stories stay small and child-facing:
- mystery: a hidden source, a trail of clues, a reveal
- rhyme: each clue is a short rhyme tied to the world state
- kindness: the mystery ends as a welcome, not a fright
- humor: the hero makes one silly wrong guess along the way

Run it
------
    python storyworlds/worlds/gpt-5.4/lonely_matey_farmyard_rhyme_kindness_humor_mystery.py
    python storyworlds/worlds/gpt-5.4/lonely_matey_farmyard_rhyme_kindness_humor_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/lonely_matey_farmyard_rhyme_kindness_humor_mystery.py --all --qa
    python storyworlds/worlds/gpt-5.4/lonely_matey_farmyard_rhyme_kindness_humor_mystery.py --json
    python storyworlds/worlds/gpt-5.4/lonely_matey_farmyard_rhyme_kindness_humor_mystery.py --verify

Reasonableness constraint
-------------------------
Not every kind surprise fits every hero. A sensible story here needs:

1. a gift or invitation that the hero would honestly like
2. a hiding spot that can actually hold that gift
3. a spot that can produce or carry the little mysterious sound that begins
   the search

So `valid_combos()` only allows `(hero, gift, spot)` triples that satisfy those
constraints. The inline ASP rules mirror the same logic and `--verify` checks
parity and runs normal story generation as a smoke test.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hen", "cow", "goat", "sheep", "duck"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"dog", "pig", "rooster", "horse"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class HeroSpec:
    id: str
    kind_name: str
    intro: str
    home: str
    step: str
    call: str
    favorite: str
    adjective: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class GiftSpec:
    id: str
    label: str
    phrase: str
    for_heroes: set[str] = field(default_factory=set)
    clue_sound: str = ""
    rhyme_first: str = ""
    rhyme_second: str = ""
    reveal_text: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class SpotSpec:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    makes_sound: bool = False
    sound_text: str = ""
    approach: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class HelperSpec:
    id: str
    type: str
    label: str
    style: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_lonely_to_listening(world: World) -> list[str]:
    hero = world.get("hero")
    clue = world.get("gift")
    if hero.memes["lonely"] < THRESHOLD or clue.meters["jingling"] < THRESHOLD:
        return []
    sig = ("listen", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["curiosity"] += 1
    return ["__listen__"]


def _r_clue_to_hope(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["found_clue"] < THRESHOLD:
        return []
    sig = ("hope", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hope"] += 1
    return ["__hope__"]


def _r_reveal_to_belonging(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.meters["reached_spot"] < THRESHOLD and helper.meters["revealed"] < THRESHOLD:
        return []
    sig = ("belonging", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["lonely"] = 0.0
    hero.memes["belonging"] += 1
    hero.memes["joy"] += 1
    helper.memes["kindness"] += 1
    return ["__belonging__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="lonely_to_listening", tag="emotion", apply=_r_lonely_to_listening),
    Rule(name="clue_to_hope", tag="emotion", apply=_r_clue_to_hope),
    Rule(name="reveal_to_belonging", tag="emotion", apply=_r_reveal_to_belonging),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def gift_fits_hero(hero_id: str, gift_id: str) -> bool:
    return hero_id in GIFTS[gift_id].for_heroes


def spot_fits_gift(gift_id: str, spot_id: str) -> bool:
    return gift_id in SPOTS[spot_id].fits


def combo_reasonable(hero_id: str, gift_id: str, spot_id: str) -> bool:
    return (
        gift_fits_hero(hero_id, gift_id)
        and spot_fits_gift(gift_id, spot_id)
        and SPOTS[spot_id].makes_sound
        and bool(GIFTS[gift_id].clue_sound)
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hero_id in HEROES:
        for gift_id in GIFTS:
            for spot_id in SPOTS:
                if combo_reasonable(hero_id, gift_id, spot_id):
                    combos.append((hero_id, gift_id, spot_id))
    return combos


def explain_rejection(hero_id: str, gift_id: str, spot_id: str) -> str:
    hero = HEROES[hero_id]
    gift = GIFTS[gift_id]
    spot = SPOTS[spot_id]
    if hero_id not in gift.for_heroes:
        return (
            f"(No story: {gift.phrase} is not a kind, sensible surprise for {hero.kind_name}."
            f" The reveal should offer something the hero would honestly enjoy.)"
        )
    if gift_id not in spot.fits:
        return (
            f"(No story: {spot.phrase} cannot reasonably hide {gift.phrase}."
            f" Pick a hiding place that can really hold the surprise.)"
        )
    if not spot.makes_sound:
        return (
            f"(No story: {spot.phrase} would not make the little mysterious sound"
            f" that starts this farmyard mystery.)"
        )
    return "(No story: this combination does not support a sensible clue trail.)"


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, hero_cfg: HeroSpec) -> None:
    hero.memes["lonely"] += 1
    world.say(
        f"In the farmyard, {hero.id} the {hero_cfg.kind_name} spent the late afternoon by "
        f"{hero_cfg.home}. {hero_cfg.intro}"
    )
    world.say(
        f"{hero.pronoun().capitalize()} was not cross and not shy exactly. "
        f"{hero.pronoun().capitalize()} was lonely, and the yard felt bigger because of it."
    )


def begin_mystery(world: World, hero: Entity, gift: Entity, spot_cfg: SpotSpec, gift_cfg: GiftSpec) -> None:
    gift.meters["jingling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {spot_cfg.sound_text} There came a tiny {gift_cfg.clue_sound} sound, "
        f"as if the farmyard itself were whispering a secret."
    )


def silly_guess(world: World, hero: Entity, helper_cfg: HelperSpec) -> None:
    hero.memes["puzzled"] += 1
    guesses = [
        "a detective turnip wearing boots",
        "a moonlit chicken band",
        "one very polite ghost in a straw hat",
    ]
    guess = world.facts.get("guess", guesses[0])
    world.say(
        f'"Who goes there?" {hero.id} asked. Then {hero.pronoun()} added, '
        f'"If you are {guess}, please say so at once."'
    )
    world.say(
        f"No answer came except a rustle and one ridiculous hiccup of a sound, which made "
        f"{hero.id} feel nervous and giggly at the same time."
    )


def find_clue(world: World, hero: Entity, gift_cfg: GiftSpec, spot_cfg: SpotSpec) -> None:
    hero.meters["found_clue"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near {spot_cfg.phrase}, {hero.id} found a little card tucked where only curious eyes "
        f"would notice it."
    )
    world.say(
        f'On it was a rhyme: "{gift_cfg.rhyme_first}, {gift_cfg.rhyme_second}."'
    )


def follow_trail(world: World, hero: Entity, spot_cfg: SpotSpec, hero_cfg: HeroSpec) -> None:
    hero.meters["reached_spot"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took {hero_cfg.step} steps across the straw and followed the clue "
        f"toward {spot_cfg.approach}."
    )
    world.say(
        f"The mystery no longer felt mean or spooky. It felt as if someone wanted "
        f"{hero.pronoun('object')} to keep coming."
    )


def reveal(world: World, hero: Entity, helper: Entity, gift: Entity,
           helper_cfg: HelperSpec, gift_cfg: GiftSpec, spot_cfg: SpotSpec) -> None:
    helper.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last the hiding place gave up its secret. Out popped {helper.id} the {helper_cfg.label}, "
        f"{helper_cfg.style}."
    )
    world.say(helper_cfg.reveal_line.format(hero=hero.id, gift=gift_cfg.label))
    world.say(
        f"Beside {helper.pronoun('object')} was {gift_cfg.phrase}. {gift_cfg.reveal_text}"
    )
    world.say(
        f'{helper.id} grinned. "I did not want you to feel lonely. Every yard needs a matey."'
    )
    world.say(
        f"{hero.id}'s ears lifted. The odd little sound, the rhyme, and the hidden trail had all been "
        f"a kind invitation."
    )
    world.say(
        f"Soon they were together in the fading light, and {spot_cfg.ending_image}"
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    hero_cfg: HeroSpec,
    gift_cfg: GiftSpec,
    spot_cfg: SpotSpec,
    helper_cfg: HelperSpec,
    hero_name: str,
    helper_name: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_cfg.id,
        label=hero_cfg.kind_name,
        role="hero",
        attrs={"favorite": hero_cfg.favorite},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        attrs={"style": helper_cfg.style},
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type=gift_cfg.id,
        label=gift_cfg.label,
        role="gift",
    ))
    spot = world.add(Entity(
        id="spot",
        kind="thing",
        type=spot_cfg.id,
        label=spot_cfg.label,
        role="spot",
    ))

    guess_pool = [
        "a detective turnip wearing boots",
        "a moonlit chicken band",
        "one very polite ghost in a straw hat",
    ]
    world.facts["guess"] = guess_pool[(len(hero_name) + len(helper_name)) % len(guess_pool)]

    introduce(world, hero, hero_cfg)

    world.para()
    begin_mystery(world, hero, gift, spot_cfg, gift_cfg)
    silly_guess(world, hero, helper_cfg)
    find_clue(world, hero, gift_cfg, spot_cfg)

    world.para()
    follow_trail(world, hero, spot_cfg, hero_cfg)
    reveal(world, hero, helper, gift, helper_cfg, gift_cfg, spot_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        gift=gift,
        spot=spot,
        hero_cfg=hero_cfg,
        helper_cfg=helper_cfg,
        gift_cfg=gift_cfg,
        spot_cfg=spot_cfg,
        mystery_started=gift.meters["jingling"] >= THRESHOLD,
        clue_found=hero.meters["found_clue"] >= THRESHOLD,
        reached_spot=hero.meters["reached_spot"] >= THRESHOLD,
        belonging=hero.memes["belonging"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HEROES = {
    "duck": HeroSpec(
        id="duck",
        kind_name="duck",
        intro="She liked the shimmer on the water trough, but today even that bright wobble did not cheer her.",
        home="the water trough",
        step="soft slap-slap",
        call="quack",
        favorite="crumbs and company",
        adjective="waddly",
        tags={"duck", "lonely"},
    ),
    "lamb": HeroSpec(
        id="lamb",
        kind_name="lamb",
        intro="She nibbled clover tips and listened to the yard, hoping someone might call her over.",
        home="the clover patch",
        step="small springy",
        call="baa",
        favorite="fresh clover and company",
        adjective="springy",
        tags={"lamb", "lonely"},
    ),
    "piglet": HeroSpec(
        id="piglet",
        kind_name="piglet",
        intro="He snuffled at the warm straw and made curly little sighs into the evening air.",
        home="the straw pen",
        step="quick pat-pat",
        call="oink",
        favorite="apple bits and company",
        adjective="snuffly",
        tags={"piglet", "lonely"},
    ),
}

GIFTS = {
    "seed_cake": GiftSpec(
        id="seed_cake",
        label="seed cake",
        phrase="a small round seed cake on a blue plate",
        for_heroes={"duck", "lamb", "piglet"},
        clue_sound="plink-plink",
        rhyme_first="Clink-clank, do not be blank",
        rhyme_second="follow the board to a friendly thank",
        reveal_text="It was meant for sharing, not gobbling alone.",
        tags={"food", "kindness"},
    ),
    "ribbon_hat": GiftSpec(
        id="ribbon_hat",
        label="ribbon hat",
        phrase="a tiny straw hat with a red ribbon",
        for_heroes={"lamb", "piglet"},
        clue_sound="jingle-jingle",
        rhyme_first="Snip-snap, no need to splat",
        rhyme_second="come find the laugh and a jaunty hat",
        reveal_text="It looked so cheerful that even the shadows seemed to smile.",
        tags={"hat", "humor"},
    ),
    "bell_bracelet": GiftSpec(
        id="bell_bracelet",
        label="bell bracelet",
        phrase="a little bell bracelet tied with twine",
        for_heroes={"duck", "lamb"},
        clue_sound="ting-ting",
        rhyme_first="Ting-ting, do not roam sadly",
        rhyme_second="step to the hay where a matey waits gladly",
        reveal_text="The tiny bells were silly and sweet, made for walking together with a merry shake.",
        tags={"bell", "humor", "kindness"},
    ),
}

SPOTS = {
    "hay_bale": SpotSpec(
        id="hay_bale",
        label="hay bale",
        phrase="the tallest hay bale",
        fits={"seed_cake", "ribbon_hat", "bell_bracelet"},
        makes_sound=True,
        sound_text="a breeze tickled the loose straw behind the hay bales.",
        approach="the crooked path by the hay shed",
        ending_image="the hay smelled warm, the sky turned purple, and the two of them looked very small and very happy there",
        tags={"hay", "mystery"},
    ),
    "wheelbarrow": SpotSpec(
        id="wheelbarrow",
        label="wheelbarrow",
        phrase="the old wheelbarrow",
        fits={"seed_cake", "ribbon_hat"},
        makes_sound=True,
        sound_text="the old wheelbarrow gave a gentle wobble and bumped its handle against the fence.",
        approach="the fence where the wheelbarrow slept on one sleepy wheel",
        ending_image="the wheelbarrow leaned crookedly beside them while they laughed so hard the chickens stared",
        tags={"wheelbarrow", "mystery"},
    ),
    "feed_bin": SpotSpec(
        id="feed_bin",
        label="feed bin",
        phrase="the wooden feed bin",
        fits={"seed_cake"},
        makes_sound=True,
        sound_text="the feed-bin lid lifted a finger-width in the breeze and tapped down again.",
        approach="the dim corner beside the grain sacks",
        ending_image="dusty gold light lay over the grain sacks while company, at last, made the whole corner glow",
        tags={"feed", "mystery"},
    ),
    "pond": SpotSpec(
        id="pond",
        label="pond edge",
        phrase="the pond edge",
        fits={"bell_bracelet"},
        makes_sound=False,
        sound_text="a frog blinked from the reeds.",
        approach="the wet bank by the pond",
        ending_image="the pond held two neat rings instead of one lonely ripple",
        tags={"pond"},
    ),
}

HELPERS = {
    "goat": HelperSpec(
        id="goat",
        type="goat",
        label="goat",
        style="with a straw stem tucked over one ear like a grand detective",
        reveal_line='"Hello, {hero}," said the goat. "I hoped the rhyme would bring you here. I brought the {gift} because secrets are nicer when they turn into smiles."',
        tags={"goat", "matey"},
    ),
    "hen": HelperSpec(
        id="hen",
        type="hen",
        label="hen",
        style="trying to look mysterious but wobbling with excitement",
        reveal_line='"Oh! I meant to stay hidden one second longer," clucked the hen. "But I could not wait. The {gift} is for you, {hero}, and also for any friend who joins us."',
        tags={"hen", "matey"},
    ),
    "pony": HelperSpec(
        id="pony",
        type="horse",
        label="pony",
        style="with a soft snort and a mouth still full of giggles",
        reveal_line='"I made the clue trail," the pony said. "A farmyard mystery needs hoofbeats, a rhyme, and a happy finish. The {gift} is part of the happy bit, {hero}."',
        tags={"pony", "matey"},
    ),
}

GIRL_NAMES = ["Daisy", "Milly", "Poppy", "Tansy", "Nell"]
BOY_NAMES = ["Pip", "Moss", "Bram", "Otis", "Toby"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hero: str
    gift: str
    spot: str
    helper: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "duck": [
        ("What sound does a duck make?",
         "A duck often says quack. Ducks also make soft splashing sounds when they waddle near water.")
    ],
    "lamb": [
        ("What sound does a lamb make?",
         "A lamb says baa. Lambs often stay close to others because they like company.")
    ],
    "piglet": [
        ("What sound does a piglet make?",
         "A piglet makes little oinks and snuffles. Piglets use their noses to explore the world around them.")
    ],
    "bell": [
        ("What does a little bell do?",
         "A little bell makes a ringing sound when it moves. That sound can help someone notice where it is.")
    ],
    "hat": [
        ("What is a straw hat for?",
         "A straw hat can shade your head from the sun. In a silly story, it can also make someone look funny and cheerful.")
    ],
    "food": [
        ("Why is sharing a snack a kind thing to do?",
         "Sharing a snack tells someone they are welcome with you. It can turn a lonely moment into a friendly one.")
    ],
    "hay": [
        ("What is a hay bale?",
         "A hay bale is a big bundle of dried grass. Farmers keep hay for animals to eat and sometimes stack it high in the yard.")
    ],
    "wheelbarrow": [
        ("What is a wheelbarrow?",
         "A wheelbarrow is a small cart with handles and usually one wheel. People use it to move heavy things around a farm or garden.")
    ],
    "feed": [
        ("What is a feed bin?",
         "A feed bin is a container that holds grain or other animal food. It keeps the food in one safe place.")
    ],
    "kindness": [
        ("What can kindness do when someone feels lonely?",
         "Kindness can help a lonely person feel seen and included. A small welcome can change the whole mood of a day.")
    ],
    "mystery": [
        ("What makes something feel like a mystery?",
         "A mystery begins when you notice something strange and do not know the answer yet. Clues help you find the answer step by step.")
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is when words have matching sounds, like ring and sing. Rhymes can make clues feel playful and easy to remember.")
    ],
}
KNOWLEDGE_ORDER = [
    "duck", "lamb", "piglet", "bell", "hat", "food",
    "hay", "wheelbarrow", "feed", "kindness", "mystery", "rhyme",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    gift_cfg = f["gift_cfg"]
    spot_cfg = f["spot_cfg"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old set in a farmyard. Include the words "lonely" and "matey".',
        f"Tell a child-facing story where {hero.id} feels lonely, hears a tiny mysterious sound near {spot_cfg.phrase}, and follows a rhyming clue to a kind surprise.",
        f"Write a funny, kind farmyard mystery where {helper.id} secretly leaves {gift_cfg.phrase} and a rhyme so that {hero.id} will not feel left out anymore.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    gift_cfg = f["gift_cfg"]
    spot_cfg = f["spot_cfg"]
    hero_cfg = f["hero_cfg"]
    helper_cfg = f["helper_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero_cfg.kind_name}, who felt lonely in the farmyard, and {helper.id} the {helper_cfg.label}, who planned a secret surprise."
        ),
        (
            f"Why did the story begin to feel like a mystery?",
            f"It began when {hero.id} heard a tiny strange sound near {spot_cfg.phrase} and could not tell where it came from. Then {hero.pronoun()} found a rhyming clue, which turned the odd sound into a trail to follow."
        ),
        (
            f"What silly thing did {hero.id} imagine?",
            f"{hero.id} wondered if the noise came from {world.facts['guess']}. That funny wrong guess made the mystery feel less scary and more playful."
        ),
        (
            f"What clue helped {hero.id} keep going?",
            f"{hero.pronoun('subject').capitalize()} found a small card with a rhyme that pointed {hero.pronoun('object')} onward. Because the clue felt friendly instead of sharp or mean, it gave {hero.pronoun('object')} hope."
        ),
        (
            f"Who made the mystery, and why?",
            f"{helper.id} made the mystery. {helper.pronoun('subject').capitalize()} wanted to welcome {hero.id} with kindness so {hero.pronoun()} would not feel lonely anymore."
        ),
        (
            f"What was waiting at the end?",
            f"At the end there was {gift_cfg.phrase} and a kind invitation to join in. The surprise mattered because it showed the mystery had been leading {hero.pronoun('object')} toward friendship all along."
        ),
        (
            "How did the story end?",
            f"It ended with the two of them together in the farmyard instead of apart. The final image proves what changed: {hero.id} was no longer lonely, because someone had made room for a matey beside {hero.pronoun('object')}."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["hero_cfg"].tags)
    tags |= set(f["gift_cfg"].tags)
    tags |= set(f["spot_cfg"].tags)
    tags |= {"kindness", "mystery", "rhyme"}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        hero="duck",
        gift="bell_bracelet",
        spot="hay_bale",
        helper="goat",
        hero_name="Daisy",
        helper_name="Maple",
    ),
    StoryParams(
        hero="lamb",
        gift="ribbon_hat",
        spot="wheelbarrow",
        helper="hen",
        hero_name="Milly",
        helper_name="Dot",
    ),
    StoryParams(
        hero="piglet",
        gift="seed_cake",
        spot="feed_bin",
        helper="pony",
        hero_name="Pip",
        helper_name="Clover",
    ),
    StoryParams(
        hero="lamb",
        gift="seed_cake",
        spot="hay_bale",
        helper="goat",
        hero_name="Poppy",
        helper_name="Thistle",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A gift fits a hero if it is meant for that kind of hero.
gift_fits_hero(H, G) :- gift_for(G, H).

% A spot fits a gift if that spot can hold it.
spot_fits_gift(G, S) :- spot_holds(S, G).

% A valid story needs a suitable gift, a real hiding place, and a place that can
% start the mystery with a sound.
valid(H, G, S) :- hero(H), gift(G), spot(S),
                  gift_fits_hero(H, G),
                  spot_fits_gift(G, S),
                  spot_makes_sound(S),
                  gift_sound(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        if gift.clue_sound:
            lines.append(asp.fact("gift_sound", gift_id))
        for hero_id in sorted(gift.for_heroes):
            lines.append(asp.fact("gift_for", gift_id, hero_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.makes_sound:
            lines.append(asp.fact("spot_makes_sound", spot_id))
        for gift_id in sorted(spot.fits):
            lines.append(asp.fact("spot_holds", spot_id, gift_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
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
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from generate()")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty default-resolved story")
        print("OK: default resolve_params() + generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a lonely farmyard animal follows a rhyming mystery to kindness."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.gift and args.spot:
        if not combo_reasonable(args.hero, args.gift, args.spot):
            raise StoryError(explain_rejection(args.hero, args.gift, args.spot))

    combos = [
        combo for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.gift is None or combo[1] == args.gift)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, gift_id, spot_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS.keys()))
    hero_kind = HEROES[hero_id].id
    if hero_kind in {"duck", "lamb"}:
        hero_name = args.hero_name or rng.choice(GIRL_NAMES)
    else:
        hero_name = args.hero_name or rng.choice(BOY_NAMES)
    helper_name = args.helper_name or rng.choice(
        [n for n in GIRL_NAMES + BOY_NAMES + ["Maple", "Clover", "Thistle", "Dot"] if n != hero_name]
    )

    return StoryParams(
        hero=hero_id,
        gift=gift_id,
        spot=spot_id,
        helper=helper_id,
        hero_name=hero_name,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"(Unknown hero: {params.hero})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not combo_reasonable(params.hero, params.gift, params.spot):
        raise StoryError(explain_rejection(params.hero, params.gift, params.spot))

    world = tell(
        hero_cfg=HEROES[params.hero],
        gift_cfg=GIFTS[params.gift],
        spot_cfg=SPOTS[params.spot],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        helper_name=params.helper_name,
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
        print(f"{len(combos)} compatible (hero, gift, spot) combos:\n")
        for hero_id, gift_id, spot_id in combos:
            print(f"  {hero_id:7} {gift_id:14} {spot_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.hero} / {p.gift} / {p.spot}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
