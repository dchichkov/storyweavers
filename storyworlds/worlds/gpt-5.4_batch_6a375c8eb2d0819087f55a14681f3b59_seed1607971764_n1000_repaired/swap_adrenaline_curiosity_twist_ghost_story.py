#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/swap_adrenaline_curiosity_twist_ghost_story.py
========================================================================

A standalone storyworld for a child-facing ghost story built around one spooky,
fixable mistake: **two treasured things were swapped**, and a restless ghost keeps
nudging the room until someone puts them back where they belong.

The stories stay small and classical:
- a child arrives in an old room,
- a ghostly sign stirs fear, curiosity, and a little adrenaline,
- the child either follows the clue or fetches a caretaker,
- the twist is that the ghost is not trying to frighten anyone at all,
- the swapped objects are restored,
- the room becomes peaceful again.

Run it
------
    python storyworlds/worlds/gpt-5.4/swap_adrenaline_curiosity_twist_ghost_story.py
    python storyworlds/worlds/gpt-5.4/swap_adrenaline_curiosity_twist_ghost_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/swap_adrenaline_curiosity_twist_ghost_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/swap_adrenaline_curiosity_twist_ghost_story.py --trace
    python storyworlds/worlds/gpt-5.4/swap_adrenaline_curiosity_twist_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4/swap_adrenaline_curiosity_twist_ghost_story.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRIGHT_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
class Room:
    id: str
    label: str
    entry: str
    atmosphere: str
    affords_pairs: set[str] = field(default_factory=set)
    affords_signs: set[str] = field(default_factory=set)
    difficulty: int = 1
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
class PairSwap:
    id: str
    label: str
    item_left: str
    item_right: str
    wrong_state: str
    clue: str
    fix_text: str
    reveal: str
    ending_image: str
    ghost_name: str
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
class Sign:
    id: str
    opening: str
    chase: str
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
class Helper:
    id: str
    label: str
    phrase: str
    glow: str
    brightness: int
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
class Response:
    id: str
    label: str
    sense: int
    solo: bool
    text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.characters() if e.role in {"hero", "companion"}]

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


def _r_haunt(world: World) -> list[str]:
    room = world.get("room")
    left_item = world.get("left_item")
    right_item = world.get("right_item")
    sign_ent = world.get("sign")
    if room.meters["spooky"] >= THRESHOLD:
        return []
    if sign_ent.meters["active"] < THRESHOLD:
        return []
    if left_item.meters["misplaced"] < THRESHOLD and right_item.meters["misplaced"] < THRESHOLD:
        return []
    room.meters["spooky"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    hero = world.get("hero")
    hero.memes["curiosity"] += 1
    hero.memes["adrenaline"] += 1
    return ["__haunt__"]


def _r_settle(world: World) -> list[str]:
    room = world.get("room")
    left_item = world.get("left_item")
    right_item = world.get("right_item")
    ghost = world.get("ghost")
    if left_item.meters["misplaced"] >= THRESHOLD or right_item.meters["misplaced"] >= THRESHOLD:
        return []
    if ("settled",) in world.fired:
        return []
    world.fired.add(("settled",))
    room.meters["spooky"] = 0.0
    room.meters["warmth"] += 1
    ghost.memes["peace"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
    return ["__settled__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="haunt", tag="emotional", apply=_r_haunt),
    Rule(name="settle", tag="resolution", apply=_r_settle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ROOMS = {
    "hallway": Room(
        id="hallway",
        label="the upstairs hallway",
        entry="At the end of supper, the old house settled into creaks and soft lamplight.",
        atmosphere="The hallway was narrow and long, with striped wallpaper and a table under two oval portraits.",
        affords_pairs={"portraits"},
        affords_signs={"whisper", "tapping"},
        difficulty=2,
        tags={"hallway", "old_house"},
    ),
    "nursery": Room(
        id="nursery",
        label="the old nursery",
        entry="When the rain tapped the windows, the oldest room in the house seemed to wake up a little.",
        atmosphere="The nursery still held a small rocking chair, a pale rug, and a shelf where two dolls watched the room.",
        affords_pairs={"dolls"},
        affords_signs={"lullaby", "pale_glow"},
        difficulty=1,
        tags={"nursery", "old_house"},
    ),
    "library": Room(
        id="library",
        label="the cedar library",
        entry="After the lamps were turned low, the library smelled like cedar wood and sleeping books.",
        atmosphere="A brass hook board hung beside the door, and below it stood a desk scattered with faded labels.",
        affords_pairs={"keys"},
        affords_signs={"whisper", "pale_glow"},
        difficulty=2,
        tags={"library", "old_house"},
    ),
}

PAIRS = {
    "portraits": PairSwap(
        id="portraits",
        label="two portraits",
        item_left="Rose's portrait",
        item_right="Iris's portrait",
        wrong_state="Someone had cleaned the hallway that morning and hung the sisters' portraits on the wrong nails.",
        clue="two pale ovals on the wallpaper showed that the portraits had once hung the other way around, and the tiny name cards no longer matched the faces beneath them",
        fix_text="carefully lifted the portraits down and made the swap, putting each sister back above her own little name card",
        reveal="A cool whisper softened into a happy sigh, as if the house had only wanted the sisters set right again.",
        ending_image="The portraits looked peaceful at last, and the hallway felt like a place for tiptoes, not shivers.",
        ghost_name="the quiet hallway ghost",
        tags={"portraits", "swap"},
    ),
    "dolls": PairSwap(
        id="dolls",
        label="two dolls",
        item_left="the blue-ribbon doll",
        item_right="the red-ribbon doll",
        wrong_state="The two dolls had been set on the wrong cushions, with each ribbon facing the blanket stitched for the other one.",
        clue="the blue blanket had little red roses sewn into one corner, while the red blanket had blue stars, and the ribbons on the dolls made the mix-up easy to see",
        fix_text="made a gentle swap, settling each doll onto the cushion and blanket that matched her ribbon",
        reveal="The pale glow melted into a warm shimmer, as if someone unseen was pleased to see the nursery tidy again.",
        ending_image="The dolls sat still and proper on their own cushions, and the nursery looked sleepy instead of strange.",
        ghost_name="the nursery ghost",
        tags={"dolls", "swap"},
    ),
    "keys": PairSwap(
        id="keys",
        label="two old keys",
        item_left="the garden key",
        item_right="the attic key",
        wrong_state="After a busy afternoon, the two old keys had been hung on the wrong hooks beside the library door.",
        clue="dust-free marks on the wood showed where the heavier attic key used to hang, and the faded paper labels were crossed under the wrong shapes",
        fix_text="reached up and made the swap, returning the garden key and the attic key to their proper hooks",
        reveal="The whisper drifted away like a page being turned, and the room seemed grateful rather than scary.",
        ending_image="The key board looked neat and sensible again, and even the shadows along the bookshelves seemed calm.",
        ghost_name="the library ghost",
        tags={"keys", "swap"},
    ),
}

SIGNS = {
    "whisper": Sign(
        id="whisper",
        opening="A whisper moved through the dark as if the room were trying to remember a name.",
        chase="Now and then the whisper slipped ahead of them, always from the place where the wrong thing was hanging.",
        tags={"whisper", "ghost"},
    ),
    "tapping": Sign(
        id="tapping",
        opening="A soft tapping came from the wall: tap... tap... pause... tap.",
        chase="The tapping quickened whenever they looked at the crooked portraits, as if patient fingers were asking them to notice.",
        tags={"tapping", "ghost"},
    ),
    "pale_glow": Sign(
        id="pale_glow",
        opening="A pale glow trembled in the corner like moonlight that had forgotten how to stay still.",
        chase="The glow hovered near the mixed-up things, then drifted away when they followed it.",
        tags={"glow", "ghost"},
    ),
    "lullaby": Sign(
        id="lullaby",
        opening="Very softly, from nowhere they could see, a tiny lullaby hummed only three notes and then stopped.",
        chase="Each time the song returned, it seemed to come from the shelf with the dolls instead of the rocking chair.",
        tags={"lullaby", "ghost"},
    ),
}

HELPERS = {
    "flashlight": Helper(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="clicked on with a clean white beam",
        brightness=3,
        tags={"flashlight"},
    ),
    "lantern": Helper(
        id="lantern",
        label="lantern",
        phrase="a battery lantern",
        glow="glowed gold and steady in small hands",
        brightness=2,
        tags={"lantern"},
    ),
    "nightlight": Helper(
        id="nightlight",
        label="night-light",
        phrase="a little night-light",
        glow="made only a pearl-sized circle in the dark",
        brightness=1,
        tags={"nightlight"},
    ),
}

RESPONSES = {
    "follow_clue": Response(
        id="follow_clue",
        label="follow the clue",
        sense=2,
        solo=True,
        text="decided to follow the spooky clue quietly and look closely before waking a grown-up",
        tags={"investigate"},
    ),
    "call_caretaker": Response(
        id="call_caretaker",
        label="call a caretaker",
        sense=3,
        solo=False,
        text="called a grown-up right away and asked for help before touching anything",
        tags={"ask_adult"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]
TRAITS = ["curious", "careful", "thoughtful", "steady", "brave"]
COMPANION_TRAITS = ["quiet", "gentle", "careful", "sleepy", "watchful"]
CARETAKER_TYPES = ["grandmother", "grandfather", "aunt", "uncle"]


def sign_fits(room: Room, sign: Sign) -> bool:
    return sign.id in room.affords_signs


def pair_fits(room: Room, pair: PairSwap) -> bool:
    return pair.id in room.affords_pairs


def helper_can_solve(room: Room, helper: Helper, response: Response) -> bool:
    if response.id == "call_caretaker":
        return helper.brightness >= BRIGHT_MIN
    return helper.brightness >= room.difficulty


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for room_id, room in ROOMS.items():
        for pair_id, pair in PAIRS.items():
            if not pair_fits(room, pair):
                continue
            for sign_id, sign in SIGNS.items():
                if not sign_fits(room, sign):
                    continue
                for helper_id, helper in HELPERS.items():
                    for response_id, response in RESPONSES.items():
                        if helper_can_solve(room, helper, response):
                            combos.append((room_id, pair_id, sign_id, helper_id, response_id))
    return combos


@dataclass
class StoryParams:
    room: str
    pair: str
    sign: str
    helper: str
    response: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    caretaker: str
    hero_trait: str
    companion_trait: str
    seed: Optional[int] = None
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


def explain_rejection(room: Room, pair: PairSwap, sign: Sign, helper: Helper, response: Response) -> str:
    if not pair_fits(room, pair):
        return (
            f"(No story: {pair.label} do not belong in {room.label}, so the room has no honest swap to fix.)"
        )
    if not sign_fits(room, sign):
        return (
            f"(No story: {sign.id.replace('_', ' ')} is not a fitting haunting sign for {room.label}. Pick a sign the room can plausibly make.)"
        )
    if not helper_can_solve(room, helper, response):
        return (
            f"(No story: {helper.phrase} is too dim for {room.label}. If the children follow the clue themselves, they need enough light to notice what was swapped.)"
        )
    return "(No story: this combination does not fit the world.)"


def outcome_of(params: StoryParams) -> str:
    response = RESPONSES[params.response]
    return "solo_fix" if response.solo else "together_fix"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def introduce(world: World, room_cfg: Room, hero: Entity, companion: Entity, caretaker: Entity) -> None:
    world.say(
        f"{room_cfg.entry} {hero.id} was staying with {caretaker.label_word}, and {companion.id} padded along beside {hero.pronoun('object')}."
    )
    world.say(
        f"{hero.id} was a {hero.traits[0]} little {hero.type}, and {companion.id} was a {companion.traits[0]} {companion.type} who did not like surprises nearly as much."
    )
    world.say(room_cfg.atmosphere)


def seed_disturbance(world: World, pair_cfg: PairSwap) -> None:
    world.say(pair_cfg.wrong_state)


def first_sign(world: World, sign_cfg: Sign) -> None:
    world.say(sign_cfg.opening)


def feel_spook(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"{companion.id} moved closer at once. {hero.id} felt a tiny spark of adrenaline skip through {hero.pronoun('possessive')} chest, but curiosity was brighter than the wish to run."
    )


def choose_helper(world: World, hero: Entity, helper_cfg: Helper, response_cfg: Response) -> None:
    world.say(
        f"{hero.id} picked up {helper_cfg.phrase} that {helper_cfg.glow}. Then {hero.pronoun()} {response_cfg.text}."
    )


def follow_sign(world: World, sign_cfg: Sign, hero: Entity, companion: Entity, room_cfg: Room) -> None:
    hero.memes["tracking"] += 1
    world.say(
        f"They stepped into {room_cfg.label}, listening hard. {sign_cfg.chase}"
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"Each little sound made {companion.id} squeeze {hero.id}'s sleeve, and that made the moment feel even more real."
        )


def spot_clue(world: World, pair_cfg: PairSwap, helper_cfg: Helper, hero: Entity) -> None:
    hero.memes["insight"] += 1
    world.say(
        f"In the steady light, {hero.id} finally saw the clue: {pair_cfg.clue}."
    )


def call_caretaker(world: World, caretaker: Entity, hero: Entity) -> None:
    world.say(
        f'"{caretaker.label_word.capitalize()}?" {hero.id} called softly. In a moment, {caretaker.label_word} came in, sleepy but kind, and listened instead of laughing.'
    )


def caretaker_understands(world: World, caretaker: Entity, pair_cfg: PairSwap) -> None:
    world.say(
        f'{caretaker.label_word.capitalize()} looked from one thing to the other and nodded slowly. "Oh," {caretaker.pronoun()} said. "I think I know what happened."'
    )
    world.say(
        f"{caretaker.label_word.capitalize()} noticed the same clue too, and suddenly the mystery no longer felt wild. It felt sad and fixable."
    )


def make_swap(world: World, pair_cfg: PairSwap, hero: Entity, caretaker: Optional[Entity]) -> None:
    left_item = world.get("left_item")
    right_item = world.get("right_item")
    left_item.meters["misplaced"] = 0.0
    right_item.meters["misplaced"] = 0.0
    left_item.meters["placed"] += 1
    right_item.meters["placed"] += 1
    actor = caretaker.label_word.capitalize() if caretaker is not None else hero.id
    if caretaker is None:
        world.say(f"{hero.id} took a careful breath and {pair_cfg.fix_text}.")
    else:
        world.say(f"{actor} and {hero.id} {pair_cfg.fix_text}.")
    propagate(world, narrate=False)


def reveal_twist(world: World, pair_cfg: PairSwap, hero: Entity, companion: Entity) -> None:
    ghost = world.get("ghost")
    ghost.memes["seen"] += 1
    world.say(
        f"For one blink, they saw only a soft shape in the air, no sharper than mist. {pair_cfg.reveal}"
    )
    world.say(
        f"That was the twist: the ghost had not wanted to scare anyone away. It had only wanted somebody curious enough to notice the swap and make it right."
    )
    if hero.memes["relief"] >= THRESHOLD:
        world.say(
            f"{hero.id} let out the breath {hero.pronoun()} had been holding, and even {companion.id} gave a shaky little smile."
        )


def closing(world: World, room_cfg: Room, pair_cfg: PairSwap, hero: Entity, caretaker: Entity, outcome: str) -> None:
    if outcome == "solo_fix":
        world.say(
            f"When {caretaker.label_word} came to tuck them in later, {hero.id} told the whole story in a whisper. {caretaker.label_word.capitalize()} listened, looked toward {room_cfg.label}, and simply kissed the top of {hero.pronoun('possessive')} head."
        )
    else:
        world.say(
            f"After that, {caretaker.label_word} kept the light on a little longer, and nobody minded. The room no longer felt hungry for attention."
        )
    world.say(pair_cfg.ending_image)


def tell(
    room_cfg: Room,
    pair_cfg: PairSwap,
    sign_cfg: Sign,
    helper_cfg: Helper,
    response_cfg: Response,
    hero_name: str,
    hero_gender: str,
    companion_name: str,
    companion_gender: str,
    caretaker_type: str,
    hero_trait: str,
    companion_trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[hero_trait],
            attrs={"stays_with": caretaker_type},
        )
    )
    companion = world.add(
        Entity(
            id=companion_name,
            kind="character",
            type=companion_gender,
            role="companion",
            traits=[companion_trait],
            attrs={},
        )
    )
    caretaker = world.add(
        Entity(
            id="Caretaker",
            kind="character",
            type=caretaker_type,
            role="caretaker",
            label="the caretaker",
            traits=["kind"],
            attrs={},
        )
    )
    room_ent = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=room_cfg.label,
            attrs={"room_id": room_cfg.id},
        )
    )
    sign_ent = world.add(
        Entity(
            id="sign",
            kind="thing",
            type="sign",
            label=sign_cfg.id,
            attrs={},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            label=pair_cfg.ghost_name,
            role="ghost",
            attrs={"pair_id": pair_cfg.id},
        )
    )
    left_item = world.add(
        Entity(
            id="left_item",
            kind="thing",
            type="keepsake",
            label=pair_cfg.item_left,
            attrs={"side": "left"},
        )
    )
    right_item = world.add(
        Entity(
            id="right_item",
            kind="thing",
            type="keepsake",
            label=pair_cfg.item_right,
            attrs={"side": "right"},
        )
    )

    room_ent.meters["spooky"] = 0.0
    room_ent.meters["warmth"] = 0.0
    sign_ent.meters["active"] = 1.0
    left_item.meters["misplaced"] = 1.0
    right_item.meters["misplaced"] = 1.0
    hero.memes["curiosity"] = 0.0
    hero.memes["adrenaline"] = 0.0
    hero.memes["fear"] = 0.0
    companion.memes["fear"] = 0.0
    ghost.memes["peace"] = 0.0

    world.facts.update(
        room_cfg=room_cfg,
        pair_cfg=pair_cfg,
        sign_cfg=sign_cfg,
        helper_cfg=helper_cfg,
        response_cfg=response_cfg,
        outcome="solo_fix" if response_cfg.solo else "together_fix",
    )

    introduce(world, room_cfg, hero, companion, caretaker)
    seed_disturbance(world, pair_cfg)

    world.para()
    first_sign(world, sign_cfg)
    propagate(world, narrate=False)
    feel_spook(world, hero, companion)
    choose_helper(world, hero, helper_cfg, response_cfg)

    world.para()
    if response_cfg.solo:
        follow_sign(world, sign_cfg, hero, companion, room_cfg)
        spot_clue(world, pair_cfg, helper_cfg, hero)
        make_swap(world, pair_cfg, hero, None)
    else:
        call_caretaker(world, caretaker, hero)
        follow_sign(world, sign_cfg, hero, companion, room_cfg)
        caretaker_understands(world, caretaker, pair_cfg)
        make_swap(world, pair_cfg, hero, caretaker)

    world.para()
    reveal_twist(world, pair_cfg, hero, companion)
    closing(world, room_cfg, pair_cfg, hero, caretaker, world.facts["outcome"])

    world.facts.update(
        hero=hero,
        companion=companion,
        caretaker=caretaker,
        ghost=ghost,
        room=room_ent,
        left_item=left_item,
        right_item=right_item,
        settled=ghost.memes["peace"] >= THRESHOLD,
        spooky_seen=room_ent.meters["warmth"] >= THRESHOLD or hero.memes["adrenaline"] >= THRESHOLD,
        fixed_by="hero" if response_cfg.solo else "hero_and_caretaker",
        used_helper=helper_cfg.label,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky kind of story where something strange seems to come from a spirit or from the past. In gentle ghost stories, the ghost is often sad or helpful instead of mean.",
        )
    ],
    "swap": [
        (
            "What does swap mean?",
            "Swap means to trade places or exchange things. If two objects are swapped by mistake, each one ends up where the other should be.",
        )
    ],
    "whisper": [
        (
            "What is a whisper?",
            "A whisper is a very soft way of speaking. People whisper when they want to be quiet or not wake someone up.",
        )
    ],
    "glow": [
        (
            "What is a glow?",
            "A glow is a soft, gentle light. It is not as sharp or bright as a lamp beam.",
        )
    ],
    "lullaby": [
        (
            "What is a lullaby?",
            "A lullaby is a soft song people sing to help someone rest or fall asleep. It is usually quiet and gentle.",
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for?",
            "A flashlight helps you see in dark places by shining a beam of light. It can make it easier to notice clues and move safely.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light that glows from inside a little case. A battery lantern gives steady light without a flame.",
        )
    ],
    "nightlight": [
        (
            "What is a night-light?",
            "A night-light is a very small light used to make darkness feel softer. It helps a room feel less scary, but it does not shine very far.",
        )
    ],
    "ask_adult": [
        (
            "Why is it smart to ask a grown-up for help?",
            "A grown-up can help you stay calm and notice what to do next. Asking for help is careful, not cowardly.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost",
    "swap",
    "whisper",
    "glow",
    "lullaby",
    "flashlight",
    "lantern",
    "nightlight",
    "ask_adult",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    room_cfg = f["room_cfg"]
    pair_cfg = f["pair_cfg"]
    sign_cfg = f["sign_cfg"]
    response_cfg = f["response_cfg"]
    hero = world.get("hero")
    caretaker = world.get("Caretaker")
    if response_cfg.solo:
        return [
            f'Write a short ghost story for a 3-to-5-year-old that includes the words "swap" and "adrenaline". Make the setting {room_cfg.label}, and let a child notice that {pair_cfg.label} were swapped.',
            f"Tell a gentle Curiosity-and-Twist ghost story where {hero.id} follows a {sign_cfg.id.replace('_', ' ')} in {room_cfg.label}, feels a little adrenaline, and discovers a harmless ghost only wants a swap fixed.",
            f"Write a spooky-but-kind story where {hero.id} uses curiosity instead of panic, notices what was wrong in the room, and gives the ghost a peaceful ending.",
        ]
    return [
        f'Write a short ghost story for a 3-to-5-year-old that includes the words "swap" and "adrenaline". Make the setting {room_cfg.label}, and let a child ask a grown-up for help with a spooky mystery.',
        f"Tell a gentle Curiosity-and-Twist ghost story where {hero.id} hears a {sign_cfg.id.replace('_', ' ')}, feels a little adrenaline, and then solves the mystery with {caretaker.label_word}.",
        f"Write a story where {pair_cfg.label} have been swapped, the haunting seems scary at first, and the twist is that the ghost only wants the room set right again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    caretaker = f["caretaker"]
    room_cfg = f["room_cfg"]
    pair_cfg = f["pair_cfg"]
    sign_cfg = f["sign_cfg"]
    helper_cfg = f["helper_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {companion.id}, and {caretaker.label_word} in {room_cfg.label}. They were the ones who heard the ghostly sign and stayed long enough to understand it.",
        ),
        (
            "What made the room seem haunted at first?",
            f"The room seemed haunted because {sign_cfg.opening[0].lower() + sign_cfg.opening[1:]} The strange sign arrived while the swapped objects were still wrong, so the room felt spooky before anyone knew why.",
        ),
        (
            f"Why did {hero.id} feel adrenaline and curiosity at the same time?",
            f"{hero.id} felt adrenaline because the sound or glow was spooky and unexpected. But curiosity stayed stronger, because {hero.pronoun('subject')} wanted to learn what the ghost was trying to show.",
        ),
        (
            "What had been swapped?",
            f"{pair_cfg.label.capitalize()} had been swapped by mistake. The clue showed that each one belonged in the other place, and fixing that mix-up was the heart of the mystery.",
        ),
    ]
    if outcome == "solo_fix":
        qa.append(
            (
                f"How did {hero.id} solve the ghost problem?",
                f"{hero.id} used {helper_cfg.phrase} to look closely and noticed that {pair_cfg.clue}. Then {hero.pronoun('subject')} fixed the swap carefully, which settled the room at once.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} call {caretaker.label_word}?",
                f"{hero.id} called {caretaker.label_word} because the haunting felt real and {hero.pronoun('subject')} wanted help before touching anything. Together they could look carefully, stay calm, and make the swap right in a safe way.",
            )
        )
    qa.append(
        (
            "What was the twist at the end?",
            f"The twist was that the ghost was not trying to be mean at all. It only wanted someone to notice the swap and put the room back the way it was meant to be.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended peacefully, with the room warm and quiet again. {pair_cfg.ending_image}",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost", "swap"}
    sign_cfg = world.facts["sign_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    response_cfg = world.facts["response_cfg"]
    tags |= set(sign_cfg.tags)
    tags |= set(helper_cfg.tags)
    tags |= set(response_cfg.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired if sig))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="hallway",
        pair="portraits",
        sign="tapping",
        helper="flashlight",
        response="follow_clue",
        hero="Lily",
        hero_gender="girl",
        companion="Ben",
        companion_gender="boy",
        caretaker="grandmother",
        hero_trait="curious",
        companion_trait="watchful",
    ),
    StoryParams(
        room="nursery",
        pair="dolls",
        sign="lullaby",
        helper="lantern",
        response="call_caretaker",
        hero="Max",
        hero_gender="boy",
        companion="Nora",
        companion_gender="girl",
        caretaker="aunt",
        hero_trait="thoughtful",
        companion_trait="gentle",
    ),
    StoryParams(
        room="library",
        pair="keys",
        sign="whisper",
        helper="flashlight",
        response="call_caretaker",
        hero="Zoe",
        hero_gender="girl",
        companion="Sam",
        companion_gender="boy",
        caretaker="grandfather",
        hero_trait="careful",
        companion_trait="quiet",
    ),
    StoryParams(
        room="nursery",
        pair="dolls",
        sign="pale_glow",
        helper="nightlight",
        response="follow_clue",
        hero="Eli",
        hero_gender="boy",
        companion="Mia",
        companion_gender="girl",
        caretaker="uncle",
        hero_trait="steady",
        companion_trait="sleepy",
    ),
]


ASP_RULES = r"""
valid(Room, Pair, Sign, Helper, Response) :-
    room(Room), pair(Pair), sign(Sign), helper(Helper), response(Response),
    affords_pair(Room, Pair),
    affords_sign(Room, Sign),
    light_ok(Room, Helper, Response).

light_ok(Room, Helper, follow_clue) :-
    difficulty(Room, D), brightness(Helper, B), B >= D.
light_ok(_Room, Helper, call_caretaker) :-
    brightness(Helper, B), bright_min(M), B >= M.

outcome(solo_fix) :- chosen_response(follow_clue).
outcome(together_fix) :- chosen_response(call_caretaker).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        lines.append(asp.fact("difficulty", room_id, room.difficulty))
        for pair_id in sorted(room.affords_pairs):
            lines.append(asp.fact("affords_pair", room_id, pair_id))
        for sign_id in sorted(room.affords_signs):
            lines.append(asp.fact("affords_sign", room_id, sign_id))
    for pair_id in PAIRS:
        lines.append(asp.fact("pair", pair_id))
    for sign_id in SIGNS:
        lines.append(asp.fact("sign", sign_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("brightness", helper_id, helper.brightness))
    for response_id in RESPONSES:
        lines.append(asp.fact("response", response_id))
    lines.append(asp.fact("bright_min", BRIGHT_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_response", params.response)
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure during verify for seed {seed}.")
            break

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
            raise StoryError("Generated empty story during smoke test.")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a gentle ghost story where a child notices a swap and sets an old room right."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--caretaker", choices=CARETAKER_TYPES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room_id = args.room
    pair_id = args.pair
    sign_id = args.sign
    helper_id = args.helper
    response_id = args.response

    if room_id and pair_id and sign_id and helper_id and response_id:
        room = ROOMS[room_id]
        pair = PAIRS[pair_id]
        sign = SIGNS[sign_id]
        helper = HELPERS[helper_id]
        response = RESPONSES[response_id]
        if (room_id, pair_id, sign_id, helper_id, response_id) not in set(valid_combos()):
            raise StoryError(explain_rejection(room, pair, sign, helper, response))

    combos = [
        combo
        for combo in valid_combos()
        if (room_id is None or combo[0] == room_id)
        and (pair_id is None or combo[1] == pair_id)
        and (sign_id is None or combo[2] == sign_id)
        and (helper_id is None or combo[3] == helper_id)
        and (response_id is None or combo[4] == response_id)
    ]
    if not combos:
        if room_id and pair_id and sign_id and helper_id and response_id:
            room = ROOMS[room_id]
            pair = PAIRS[pair_id]
            sign = SIGNS[sign_id]
            helper = HELPERS[helper_id]
            response = RESPONSES[response_id]
            raise StoryError(explain_rejection(room, pair, sign, helper, response))
        raise StoryError("(No valid combination matches the given options.)")

    room_id, pair_id, sign_id, helper_id, response_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    companion_name = _pick_name(rng, companion_gender, avoid=hero_name)
    caretaker = args.caretaker or rng.choice(CARETAKER_TYPES)
    hero_trait = rng.choice(TRAITS)
    companion_trait = rng.choice(COMPANION_TRAITS)
    return StoryParams(
        room=room_id,
        pair=pair_id,
        sign=sign_id,
        helper=helper_id,
        response=response_id,
        hero=hero_name,
        hero_gender=hero_gender,
        companion=companion_name,
        companion_gender=companion_gender,
        caretaker=caretaker,
        hero_trait=hero_trait,
        companion_trait=companion_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Invalid room: {params.room})")
    if params.pair not in PAIRS:
        raise StoryError(f"(Invalid pair: {params.pair})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Invalid sign: {params.sign})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")
    combo = (params.room, params.pair, params.sign, params.helper, params.response)
    if combo not in set(valid_combos()):
        raise StoryError(
            explain_rejection(
                ROOMS[params.room],
                PAIRS[params.pair],
                SIGNS[params.sign],
                HELPERS[params.helper],
                RESPONSES[params.response],
            )
        )

    world = tell(
        room_cfg=ROOMS[params.room],
        pair_cfg=PAIRS[params.pair],
        sign_cfg=SIGNS[params.sign],
        helper_cfg=HELPERS[params.helper],
        response_cfg=RESPONSES[params.response],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        companion_name=params.companion,
        companion_gender=params.companion_gender,
        caretaker_type=params.caretaker,
        hero_trait=params.hero_trait,
        companion_trait=params.companion_trait,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, pair, sign, helper, response) combos:\n")
        for room_id, pair_id, sign_id, helper_id, response_id in combos:
            print(f"  {room_id:8} {pair_id:10} {sign_id:10} {helper_id:10} {response_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} in {p.room}: {p.pair} / {p.sign} / {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
