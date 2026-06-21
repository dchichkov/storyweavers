#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/inspire_likely_surprise_mystery.py
=============================================================

A small mystery-flavored storyworld about a child whose special message goes
missing just before it can be shared. The child made the message to inspire
other people, so the disappearance matters. A clue, a helper, and a surprise
explanation drive the plot.

The world enforces a simple reasonableness rule: a setting must actually permit
the cause, the clue must match that cause, and the hiding place must be one the
cause could plausibly lead to. The story is then rendered from simulated state,
not from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/inspire_likely_surprise_mystery.py
    python storyworlds/worlds/gpt-5.4/inspire_likely_surprise_mystery.py --setting library
    python storyworlds/worlds/gpt-5.4/inspire_likely_surprise_mystery.py --cause kitten --clue pawprint
    python storyworlds/worlds/gpt-5.4/inspire_likely_surprise_mystery.py --all
    python storyworlds/worlds/gpt-5.4/inspire_likely_surprise_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/inspire_likely_surprise_mystery.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian_f", "teacher_f"}
        male = {"boy", "father", "man", "librarian_m", "teacher_m", "janitor_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    display_spot: str
    afford_causes: set[str] = field(default_factory=set)
    afford_places: set[str] = field(default_factory=set)


@dataclass
class ItemConfig:
    id: str
    label: str
    phrase: str
    make_text: str
    share_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    action_text: str
    reveal_text: str
    clue_options: set[str] = field(default_factory=set)
    place_options: set[str] = field(default_factory=set)
    setting_options: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    discovery_text: str
    follow_text: str
    explanation_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    found_text: str
    setting_options: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    entrance_text: str
    method_text: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    hero = world.entities.get("hero")
    item = world.entities.get("item")
    if not hero or not item:
        return []
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_clue_hope(world: World) -> list[str]:
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    clue = world.entities.get("clue")
    if not hero or not helper or not clue:
        return []
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_hope", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hope"] += 1
    helper.memes["focus"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    item = world.entities.get("item")
    if not hero or not item:
        return []
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    item.meters["displayed"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_hope),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


SETTINGS = {
    "library": Setting(
        id="library",
        place="the library",
        scene="Tall shelves made soft corners of shadow, and every small sound seemed important.",
        display_spot="the reading table by the window",
        afford_causes={"breeze", "kitten", "tidyup"},
        afford_places={"windowsill", "book_cart", "puppet_basket"},
    ),
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        scene="Morning light slanted across cubbies and desks, turning the room into a place full of clues.",
        display_spot="the class sharing wall",
        afford_causes={"breeze", "tidyup"},
        afford_places={"windowsill", "supply_shelf", "book_cart"},
    ),
    "garden": Setting(
        id="garden",
        place="the school garden shed",
        scene="Seed packets, tools, and pots made neat little rows, but the quiet corners still felt mysterious.",
        display_spot="the potting bench",
        afford_causes={"breeze", "tidyup"},
        afford_places={"windowsill", "seed_crate", "supply_shelf"},
    ),
}

ITEMS = {
    "card": ItemConfig(
        id="card",
        label="card",
        phrase="a bright little card with the word inspire painted in blue",
        make_text="painted the word inspire in careful blue letters and drew a yellow sun beside it",
        share_text="wanted to set it out where it could inspire anyone who felt shy about reading",
        ending_text="the blue word inspire shone from the table like a tiny brave flag",
        tags={"card", "inspire"},
    ),
    "bookmark": ItemConfig(
        id="bookmark",
        label="bookmark",
        phrase="a tall paper bookmark with inspire written down the side",
        make_text="wrote inspire down the side in silver crayon and added stars at the top",
        share_text="wanted to tuck it into a favorite book so it could inspire the next reader",
        ending_text="the bookmark peeked from the book like a secret promise to keep going",
        tags={"bookmark", "inspire"},
    ),
    "sign": ItemConfig(
        id="sign",
        label="sign",
        phrase="a small hand-lettered sign that said inspire",
        make_text="cut a neat sign from stiff paper and lettered inspire across the middle",
        share_text="wanted to prop it up so it could inspire the room before everyone arrived",
        ending_text="the little sign stood straight again, making the whole corner feel brighter",
        tags={"sign", "inspire"},
    ),
}

CAUSES = {
    "breeze": Cause(
        id="breeze",
        label="a sneaky breeze",
        action_text="A small draft had teased the paper loose and sent it gliding away.",
        reveal_text="It had not been stolen at all. A breeze from the open window had carried it off on a quiet paper flight.",
        clue_options={"ribbon", "leaf"},
        place_options={"windowsill", "book_cart"},
        setting_options={"library", "classroom", "garden"},
        tags={"air", "window"},
    ),
    "tidyup": Cause(
        id="tidyup",
        label="a careful clean-up",
        action_text="Someone had tucked the paper away while straightening the room.",
        reveal_text="The surprise was that nobody had hidden it on purpose. During a careful tidy-up, it had been set somewhere safe and simply forgotten.",
        clue_options={"paperclip", "chalk"},
        place_options={"supply_shelf", "seed_crate", "book_cart"},
        setting_options={"library", "classroom", "garden"},
        tags={"tidy", "safe"},
    ),
    "kitten": Cause(
        id="kitten",
        label="the library kitten",
        action_text="A curious kitten had batted the paper and chased it with dancing paws.",
        reveal_text="The surprise was not a thief at all, but the library kitten. It had pounced on the fluttering paper and pushed it into a hiding place.",
        clue_options={"pawprint", "ribbon"},
        place_options={"puppet_basket", "book_cart"},
        setting_options={"library"},
        tags={"animal", "playful"},
    ),
}

CLUES = {
    "ribbon": Clue(
        id="ribbon",
        label="a dangling ribbon",
        discovery_text="Near the floor, a loose ribbon from the paper twitched in a draft.",
        follow_text="The tiny ribbon pointed the way like a little finger.",
        explanation_text="A moving ribbon meant the paper had not walked away by itself; something light and playful had tugged it along.",
        tags={"air", "trail"},
    ),
    "leaf": Clue(
        id="leaf",
        label="a dry leaf",
        discovery_text="A dry leaf lay on the floor beside the empty spot, though no leaf had been there before.",
        follow_text="If a leaf had blown in, the paper was likely to have blown too.",
        explanation_text="The leaf made the open window matter. It showed that air had been moving through the room.",
        tags={"air", "window"},
    ),
    "paperclip": Clue(
        id="paperclip",
        label="a silver paperclip",
        discovery_text="A silver paperclip sat by itself on the table, as if it had slipped off in a hurry.",
        follow_text="That made it look likely the paper had been gathered up with other things during clean-up.",
        explanation_text="A paperclip is a tidy clue. It suggests sorting, stacking, and putting papers away.",
        tags={"tidy", "desk"},
    ),
    "chalk": Clue(
        id="chalk",
        label="a chalky smudge",
        discovery_text="There was a chalky white smudge near the empty place and another on a high shelf.",
        follow_text="The two smudges looked like steps in a path.",
        explanation_text="Matching smudges suggest that the same hands carried the paper from one place to another.",
        tags={"tidy", "shelf"},
    ),
    "pawprint": Clue(
        id="pawprint",
        label="a dusty pawprint",
        discovery_text="On the floor, a tiny dusty pawprint curved away between the chairs.",
        follow_text="Mysteries feel different when the clue has whiskers.",
        explanation_text="A pawprint means an animal touched the scene. The paper was likely nudged, chased, or batted away.",
        tags={"animal", "trail"},
    ),
}

PLACES = {
    "windowsill": Place(
        id="windowsill",
        label="windowsill",
        phrase="the wide windowsill behind the curtain",
        found_text="Behind the curtain, the paper had landed flat on the windowsill and waited there like a sleeping bird.",
        setting_options={"library", "classroom", "garden"},
        tags={"window"},
    ),
    "book_cart": Place(
        id="book_cart",
        label="book cart",
        phrase="the rolling book cart",
        found_text="On the lower shelf of the book cart, the paper was tucked between two large books.",
        setting_options={"library", "classroom"},
        tags={"books", "wheels"},
    ),
    "puppet_basket": Place(
        id="puppet_basket",
        label="puppet basket",
        phrase="the big basket of puppets",
        found_text="Under a floppy lion puppet, the paper lay bent but safe.",
        setting_options={"library"},
        tags={"basket", "play"},
    ),
    "supply_shelf": Place(
        id="supply_shelf",
        label="supply shelf",
        phrase="the high shelf with glue and string",
        found_text="On the high supply shelf, the paper sat beside tape and scissors, put away too neatly to be seen from below.",
        setting_options={"classroom", "garden"},
        tags={"shelf", "tidy"},
    ),
    "seed_crate": Place(
        id="seed_crate",
        label="seed crate",
        phrase="the wooden crate of seed packets",
        found_text="Inside the seed crate, the paper rested on top of the packets as if it had joined the labels.",
        setting_options={"garden"},
        tags={"garden", "crate"},
    ),
}

HELPERS = {
    "friend": Helper(
        id="friend",
        type="girl",
        label="friend",
        entrance_text="Just then a friend came over and lowered her voice as if mysteries needed softer words.",
        method_text="Together they looked low, then high, and then where small clues would be easy to miss.",
        tags={"friend"},
    ),
    "teacher": Helper(
        id="teacher",
        type="teacher_f",
        label="teacher",
        entrance_text="Their teacher noticed the worried face at once and came over quietly.",
        method_text="She did not guess wildly. She asked what had changed, then followed the clue one careful step at a time.",
        tags={"teacher"},
    ),
    "librarian": Helper(
        id="librarian",
        type="librarian_f",
        label="librarian",
        entrance_text="The librarian glided over between the shelves as if she already knew how to listen to secrets.",
        method_text="She studied the clue, glanced around the room, and checked the places where light things often drifted or were tucked away.",
        tags={"librarian"},
    ),
    "caretaker": Helper(
        id="caretaker",
        type="janitor_m",
        label="caretaker",
        entrance_text="The school caretaker paused in the doorway with a dustpan and gave the room a sharp, kind look.",
        method_text="He knew where lost papers liked to hide after busy mornings, so he searched the quiet edges first.",
        tags={"caretaker"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Noah", "Eli", "Theo", "Jack", "Owen"]
TRAITS = ["curious", "gentle", "careful", "bright", "hopeful", "thoughtful"]


def valid_combo(setting_id: str, cause_id: str, clue_id: str, place_id: str) -> bool:
    if setting_id not in SETTINGS or cause_id not in CAUSES or clue_id not in CLUES or place_id not in PLACES:
        return False
    setting = SETTINGS[setting_id]
    cause = CAUSES[cause_id]
    place = PLACES[place_id]
    return (
        cause_id in setting.afford_causes
        and place_id in setting.afford_places
        and clue_id in cause.clue_options
        and place_id in cause.place_options
        and setting_id in cause.setting_options
        and setting_id in place.setting_options
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in sorted(SETTINGS):
        for cause_id in sorted(CAUSES):
            for clue_id in sorted(CLUES):
                for place_id in sorted(PLACES):
                    if valid_combo(setting_id, cause_id, clue_id, place_id):
                        combos.append((setting_id, cause_id, clue_id, place_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    cause: str
    clue: str
    place: str
    item: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="library",
        cause="kitten",
        clue="pawprint",
        place="puppet_basket",
        item="bookmark",
        helper="librarian",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        setting="classroom",
        cause="breeze",
        clue="leaf",
        place="windowsill",
        item="sign",
        helper="teacher",
        name="Ben",
        gender="boy",
        parent="father",
        trait="thoughtful",
    ),
    StoryParams(
        setting="garden",
        cause="tidyup",
        clue="chalk",
        place="seed_crate",
        item="card",
        helper="caretaker",
        name="Maya",
        gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        setting="library",
        cause="breeze",
        clue="ribbon",
        place="book_cart",
        item="card",
        helper="friend",
        name="Theo",
        gender="boy",
        parent="father",
        trait="hopeful",
    ),
]


def explain_rejection(setting_id: str, cause_id: str, clue_id: str, place_id: str) -> str:
    if setting_id not in SETTINGS:
        return "(No story: unknown setting.)"
    if cause_id not in CAUSES:
        return "(No story: unknown cause.)"
    if clue_id not in CLUES:
        return "(No story: unknown clue.)"
    if place_id not in PLACES:
        return "(No story: unknown hiding place.)"
    setting = SETTINGS[setting_id]
    cause = CAUSES[cause_id]
    if cause_id not in setting.afford_causes:
        return (
            f"(No story: {cause.label} does not fit {setting.place}. "
            f"Pick a cause the setting can actually support.)"
        )
    if place_id not in setting.afford_places:
        return (
            f"(No story: {PLACES[place_id].phrase} is not a plausible hiding place in {setting.place}.)"
        )
    if clue_id not in cause.clue_options:
        return (
            f"(No story: the clue '{clue_id}' does not match {cause.label}. "
            f"The mystery clue should point honestly to the cause.)"
        )
    if place_id not in cause.place_options:
        return (
            f"(No story: {cause.label} would not likely lead the paper to {PLACES[place_id].phrase}.)"
        )
    return "(No story: this setting, cause, clue, and place do not belong together.)"


def introduce(world: World, hero: Entity, parent: Entity, item_cfg: ItemConfig) -> None:
    world.say(
        f"{hero.id} was a little {hero.attrs.get('trait', hero.type)} {hero.type} who liked making small things for other people."
    )
    world.say(world.setting.scene)
    world.say(
        f"That morning, {hero.id} {item_cfg.make_text}. {hero.pronoun('subject').capitalize()} made it for {parent.label_word} and everyone else, because {hero.pronoun('subject')} hoped it might inspire a brave thought in somebody's day."
    )


def place_item(world: World, hero: Entity, item: Entity, item_cfg: ItemConfig) -> None:
    item.meters["placed"] += 1
    world.say(
        f"{hero.id} carried the {item_cfg.label} to {world.setting.display_spot} and {item_cfg.share_text}."
    )


def vanish(world: World, hero: Entity, item: Entity) -> None:
    item.meters["missing"] += 1
    propagate(world)
    world.say(
        f"But when {hero.pronoun('subject')} turned back after one small errand, the {item.label} was gone."
    )
    world.say(
        f"For one puzzled moment, it seemed likely that someone had taken it, and the room felt full of quiet questions."
    )


def discover_clue(world: World, hero: Entity, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    propagate(world)
    world.say(
        f"{hero.id} looked again, slower this time. {clue_cfg.discovery_text}"
    )
    world.say(clue_cfg.follow_text)


def helper_arrives(world: World, hero: Entity, helper: Entity, helper_cfg: Helper) -> None:
    helper.memes["care"] += 1
    world.say(helper_cfg.entrance_text)
    world.say(helper_cfg.method_text)
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id} explained that the little message mattered because {hero.pronoun('subject')} had made it to inspire someone who might need a kind surprise."
        )


def follow_clue(world: World, clue_cfg: Clue, place_cfg: Place) -> None:
    world.say(
        f"{clue_cfg.explanation_text} So they checked {place_cfg.phrase}."
    )


def find_item(world: World, hero: Entity, item: Entity, cause_cfg: Cause, place_cfg: Place) -> None:
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    propagate(world)
    world.say(place_cfg.found_text)
    world.say(cause_cfg.reveal_text)
    world.say(
        f"{hero.id} gave a little laugh of relief. The mystery had felt big, but the truth was gentler than {hero.pronoun('subject')} had feared."
    )


def ending(world: World, hero: Entity, helper: Entity, item_cfg: ItemConfig) -> None:
    world.say(
        f"Together they set the {item_cfg.label} back in place. Soon {item_cfg.ending_text}."
    )
    if helper.label == "friend":
        world.say(
            f"When the first child noticed it and smiled, {hero.id} felt proud that a lost thing had still found its way to the right heart."
        )
    else:
        world.say(
            f"When other people came in and noticed it, the whole room felt calmer and brighter, just as {hero.id} had hoped."
        )


def tell(
    setting: Setting,
    cause_cfg: Cause,
    clue_cfg: Clue,
    place_cfg: Place,
    item_cfg: ItemConfig,
    helper_cfg: Helper,
    hero_name: str,
    hero_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            attrs={"trait": trait},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label={"mother": "mom", "father": "dad"}[parent_type],
            role="parent",
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type=item_cfg.id,
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="item",
            tags=set(item_cfg.tags),
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            kind="thing",
            type=clue_cfg.id,
            label=clue_cfg.label,
            role="clue",
            tags=set(clue_cfg.tags),
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            role="helper",
            tags=set(helper_cfg.tags),
        )
    )

    introduce(world, hero, parent, item_cfg)
    place_item(world, hero, item, item_cfg)

    world.para()
    vanish(world, hero, item)
    discover_clue(world, hero, clue_cfg)

    world.para()
    helper_arrives(world, hero, helper, helper_cfg)
    follow_clue(world, clue_cfg, place_cfg)
    find_item(world, hero, item, cause_cfg, place_cfg)

    world.para()
    ending(world, hero, helper, item_cfg)

    world.facts.update(
        hero=hero,
        parent=parent,
        item=item,
        clue=clue,
        helper=helper,
        setting=setting,
        cause=cause_cfg,
        clue_cfg=clue_cfg,
        place_cfg=place_cfg,
        item_cfg=item_cfg,
        solved=item.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "inspire": [
        (
            "What does inspire mean?",
            "To inspire someone is to give them a brave, hopeful, or creative feeling. A kind word or a bright idea can inspire people."
        )
    ],
    "window": [
        (
            "How can a breeze move paper?",
            "Paper is light, so moving air can lift it, slide it, or flip it into a new place. That is why loose papers should be weighed down."
        )
    ],
    "animal": [
        (
            "Why do kittens bat at paper?",
            "Kittens like small things that flutter and slide because they seem alive and playful. A paper corner can look like a tiny moving toy."
        )
    ],
    "tidy": [
        (
            "Why do things get lost during clean-up?",
            "During clean-up, people move many objects quickly into neat piles or shelves. Something small can be put somewhere safe and then forgotten."
        )
    ],
    "books": [
        (
            "Why can papers hide in a book cart?",
            "A book cart has shelves, gaps, and big books that can cover something flat. A paper can slip in and be hard to notice."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a mystery, clues point toward what really happened."
        )
    ],
}
KNOWLEDGE_ORDER = ["inspire", "clue", "window", "animal", "tidy", "books"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    cause = f["cause"]
    setting = f["setting"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "inspire" and "likely".',
        f"Tell a gentle surprise mystery where a {hero.type} makes {item_cfg.phrase} in {setting.place}, then it disappears and a clue leads to a kind explanation.",
        f"Write a child-facing mystery in which the missing object was meant to inspire someone, and the likely culprit turns out to be {cause.label} rather than a mean person.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    item_cfg = f["item_cfg"]
    clue_cfg = f["clue_cfg"]
    cause = f["cause"]
    place_cfg = f["place_cfg"]
    helper = f["helper"]
    setting = f["setting"]
    hero_name = hero.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a little {hero.type} who made {item_cfg.phrase}. {hero.pronoun('subject').capitalize()} wanted it to inspire other people."
        ),
        (
            f"Why did {hero_name} care when the {item_cfg.label} went missing?",
            f"{hero_name} had made it with care and hoped it would encourage someone else. Losing it felt important because the kind message could not be shared."
        ),
        (
            f"What clue did {hero_name} find?",
            f"{hero_name} found {clue_cfg.label}. That clue mattered because it pointed toward what had really moved the paper."
        ),
        (
            f"Who helped solve the mystery?",
            f"The {helper.label} helped solve it. {helper.pronoun('subject').capitalize()} stayed calm and followed the clue instead of making a wild guess."
        ),
        (
            "What was the surprise?",
            f"The surprise was that nobody had stolen the {item_cfg.label}. {cause.reveal_text}"
        ),
        (
            f"Where was the {item_cfg.label} found?",
            f"It was found in {place_cfg.phrase}. That hiding place fit the clue and the real cause of the mystery."
        ),
        (
            "How did the story end?",
            f"The {item_cfg.label} was put back at {setting.display_spot}, and people could finally see it. The ending shows that the lost message still got to inspire someone."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"inspire", "clue"}
    cause = world.facts["cause"]
    place_cfg = world.facts["place_cfg"]
    if "window" in cause.tags or "air" in cause.tags or "window" in place_cfg.tags:
        tags.add("window")
    if "animal" in cause.tags:
        tags.add("animal")
    if "tidy" in cause.tags:
        tags.add("tidy")
    if "books" in place_cfg.tags:
        tags.add("books")
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, Cl, P) :-
    setting(S), cause(C), clue(Cl), place(P),
    setting_cause(S, C),
    setting_place(S, P),
    cause_clue(C, Cl),
    cause_place(C, P).

bad_combo(S, C, Cl, P) :-
    setting(S), cause(C), clue(Cl), place(P),
    not valid(S, C, Cl, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cause_id in sorted(setting.afford_causes):
            lines.append(asp.fact("setting_cause", sid, cause_id))
        for place_id in sorted(setting.afford_places):
            lines.append(asp.fact("setting_place", sid, place_id))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for clue_id in sorted(cause.clue_options):
            lines.append(asp.fact("cause_clue", cid, clue_id))
        for place_id in sorted(cause.place_options):
            lines.append(asp.fact("cause_place", cid, place_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        sample = generate(resolve_params(default_args, random.Random(0)))
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded for a default random story.")
    except Exception as err:  # pragma: no cover - verification surface
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
        except Exception as err:  # pragma: no cover - verification surface
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
            break
    else:
        print(f"OK: curated generation succeeded for {len(smoke_cases)} stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a missing message, a clue, and a kind surprise ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cause and args.clue and args.place:
        if not valid_combo(args.setting, args.cause, args.clue, args.place):
            raise StoryError(explain_rejection(args.setting, args.cause, args.clue, args.place))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
        and (args.place is None or combo[3] == args.place)
    ]
    if not combos:
        guessed_setting = args.setting or next(iter(SETTINGS))
        guessed_cause = args.cause or next(iter(CAUSES))
        guessed_clue = args.clue or next(iter(CLUES))
        guessed_place = args.place or next(iter(PLACES))
        raise StoryError(explain_rejection(guessed_setting, guessed_cause, guessed_clue, guessed_place))

    setting_id, cause_id, clue_id, place_id = rng.choice(sorted(combos))
    item_id = args.item or rng.choice(sorted(ITEMS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        cause=cause_id,
        clue=clue_id,
        place=place_id,
        item=item_id,
        helper=helper_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def _require_key(registry: dict, key: str, field_name: str):
    if key not in registry:
        raise StoryError(f"(Invalid {field_name}: {key})")
    return registry[key]


def generate(params: StoryParams) -> StorySample:
    setting = _require_key(SETTINGS, params.setting, "setting")
    cause_cfg = _require_key(CAUSES, params.cause, "cause")
    clue_cfg = _require_key(CLUES, params.clue, "clue")
    place_cfg = _require_key(PLACES, params.place, "place")
    item_cfg = _require_key(ITEMS, params.item, "item")
    helper_cfg = _require_key(HELPERS, params.helper, "helper")
    if not valid_combo(params.setting, params.cause, params.clue, params.place):
        raise StoryError(explain_rejection(params.setting, params.cause, params.clue, params.place))
    world = tell(
        setting=setting,
        cause_cfg=cause_cfg,
        clue_cfg=clue_cfg,
        place_cfg=place_cfg,
        item_cfg=item_cfg,
        helper_cfg=helper_cfg,
        hero_name=params.name,
        hero_gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (setting, cause, clue, place) combos:\n")
        for setting_id, cause_id, clue_id, place_id in combos:
            print(f"  {setting_id:10} {cause_id:8} {clue_id:10} {place_id}")
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
            header = f"### {p.name}: {p.setting} / {p.cause} / {p.clue} / {p.place}"
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
