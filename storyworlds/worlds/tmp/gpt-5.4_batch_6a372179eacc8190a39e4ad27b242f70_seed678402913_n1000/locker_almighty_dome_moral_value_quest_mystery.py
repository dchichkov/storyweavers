#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/locker_almighty_dome_moral_value_quest_mystery.py
=============================================================================

A tiny nursery-rhyme-flavored storyworld about a missing object, a little quest,
and a mystery solved by patient clue-following instead of blame.

The world always includes:
- a locker
- an almighty dome
- a quest
- a mystery to solve
- a gentle moral value about honesty, patience, apology, and sharing

Run it
------
    python storyworlds/worlds/gpt-5.4/locker_almighty_dome_moral_value_quest_mystery.py
    python storyworlds/worlds/gpt-5.4/locker_almighty_dome_moral_value_quest_mystery.py --place moon_dome --item map --cause breeze
    python storyworlds/worlds/gpt-5.4/locker_almighty_dome_moral_value_quest_mystery.py --all
    python storyworlds/worlds/gpt-5.4/locker_almighty_dome_moral_value_quest_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/locker_almighty_dome_moral_value_quest_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/locker_almighty_dome_moral_value_quest_mystery.py --json
    python storyworlds/worlds/gpt-5.4/locker_almighty_dome_moral_value_quest_mystery.py --verify
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
CALM_TRAITS = {"patient", "gentle", "careful", "truthful"}


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    intro: str
    dome_line: str
    closing_image: str
    flags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    needed_for: str
    clue_word: str
    shape_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    rhyme_line: str
    clue_text: str
    spot: str
    reveal_text: str
    needs_place_flags: set[str] = field(default_factory=set)
    needs_item_tags: set[str] = field(default_factory=set)
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"seeker", "friend"}]

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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__worry__"]


def _r_blame_hurts(world: World) -> list[str]:
    seeker = world.get("seeker")
    friend = world.get("friend")
    if seeker.memes["blame"] < THRESHOLD:
        return []
    sig = ("blame_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    return ["__hurt__"]


def _r_clue_hope(world: World) -> list[str]:
    clue = world.get("clue")
    if clue.meters["found"] < THRESHOLD:
        return []
    sig = ("clue_hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["hope"] += 1
    return ["__hope__"]


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="blame_hurts", tag="social", apply=_r_blame_hurts),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_hope),
    Rule(name="found_relief", tag="resolution", apply=_r_found_relief),
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


def valid_combo(place: Place, item: MissingItem, cause: Cause) -> bool:
    return cause.needs_place_flags.issubset(place.flags) and cause.needs_item_tags.issubset(item.tags)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for cause_id, cause in CAUSES.items():
                if valid_combo(place, item, cause):
                    out.append((place_id, item_id, cause_id))
    return out


def outcome_of(params: "StoryParams") -> str:
    return "gentle" if params.trait in CALM_TRAITS else "sting"


def predict_feelings(trait: str) -> dict[str, bool]:
    return {"blame": trait not in CALM_TRAITS}


def introduce(world: World, place: Place, seeker: Entity, friend: Entity, parent: Entity) -> None:
    world.say(
        f"In {place.label}, where children skipped in a ring, "
        f"{seeker.id} and {friend.id} came with a spring."
    )
    world.say(place.intro)
    world.say(
        f'Above them shone the almighty dome, round as the moon above a home, '
        f'and even {parent.label_word} smiled to hear their humming feet.'
    )
    world.say(place.dome_line)


def set_quest(world: World, item_cfg: MissingItem, seeker: Entity, friend: Entity) -> None:
    item = world.get("item")
    locker = world.get("locker")
    locker.meters["open"] += 1
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Inside the little locker lay room for {item_cfg.phrase}, but not the thing itself."
    )
    world.say(
        f'"Oh dear," said {seeker.id}, "we need it for {item_cfg.needed_for}." '
        f'"Come, {friend.id}, let us quest before the song grows still."'
    )


def first_guess(world: World, seeker: Entity, friend: Entity, trait: str, item_cfg: MissingItem) -> None:
    if trait in CALM_TRAITS:
        seeker.memes["patience"] += 1
        friend.memes["trust"] += 1
        world.say(
            f"{seeker.id} took one slow breath and one slow look. "
            f'"A mystery should be solved with eyes, not with a pointing hand," '
            f'{seeker.pronoun()} said.'
        )
    else:
        seeker.memes["blame"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{seeker.id} stamped once lightly on the floor. "
            f'"Did you take the {item_cfg.label}?" {seeker.pronoun()} asked too fast.'
        )
        world.say(
            f'{friend.id} blinked and held both hands up. "No," {friend.pronoun()} said, '
            f'"I only came to sing."'
        )


def find_clue(world: World, cause: Cause, seeker: Entity, friend: Entity) -> None:
    clue = world.get("clue")
    clue.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {friend.id} bent low by the locker and found {cause.clue_text}."
    )
    world.say(
        f'"Look," said {friend.id}, "the clue says hush, and points us where to go."'
    )
    world.facts["clue_found"] = True


def follow_quest(world: World, cause: Cause, place: Place, seeker: Entity, friend: Entity) -> None:
    seeker.meters["steps"] += 1
    friend.meters["steps"] += 1
    world.say(
        f"So off they went on their tiny quest, through {place.label} from east to west, "
        f"following the clue toward {cause.spot}."
    )


def reveal_item(world: World, cause: Cause, seeker: Entity, friend: Entity, item_cfg: MissingItem) -> None:
    item = world.get("item")
    item.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(cause.reveal_text.format(item=item_cfg.label))
    world.say(
        f'"There you are, dear {item_cfg.label}!" cried {friend.id}. '
        f'"The mystery was a muddle, not a meanness."'
    )


def apology_or_praise(world: World, seeker: Entity, friend: Entity, trait: str) -> None:
    if trait in CALM_TRAITS:
        seeker.memes["kindness"] += 1
        friend.memes["kindness"] += 1
        world.say(
            f'{friend.id} grinned. "{seeker.id}, you were right to wait and see." '
            f'Together they nodded, glad they had let the clue speak first.'
        )
    else:
        seeker.memes["sorry"] += 1
        seeker.memes["lesson"] += 1
        friend.memes["forgive"] += 1
        world.say(
            f'{seeker.id} looked small for half a beat. "I am sorry I guessed before I knew," '
            f'{seeker.pronoun()} said.'
        )
        world.say(
            f'{friend.id} touched {seeker.pronoun("possessive")} sleeve and smiled. '
            f'"A true friend mends a hasty word with an honest one."'
        )


def ending(world: World, place: Place, item_cfg: MissingItem, seeker: Entity, friend: Entity, parent: Entity) -> None:
    seeker.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"They carried the {item_cfg.label} back to the locker, then out again for {item_cfg.needed_for}."
    )
    world.say(
        f'{parent.label_word.capitalize()} clapped softly. "The best key for any locker is truth," '
        f'{parent.pronoun()} said. "The best song under an almighty dome is one sung kindly."'
    )
    world.say(place.closing_image.format(seeker=seeker.id, friend=friend.id, item=item_cfg.label))


def tell(place: Place, item_cfg: MissingItem, cause: Cause,
         seeker_name: str = "Mina", seeker_type: str = "girl",
         friend_name: str = "Toby", friend_type: str = "boy",
         parent_type: str = "mother", trait: str = "patient") -> World:
    world = World()
    seeker = world.add(Entity(id="seeker", kind="character", type=seeker_type, label=seeker_name, phrase=seeker_name, role="seeker"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, phrase=friend_name, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", phrase="the parent", role="parent"))
    locker = world.add(Entity(id="locker", type="locker", label="locker", phrase="the little locker"))
    item = world.add(Entity(id="item", type="item", label=item_cfg.label, phrase=item_cfg.phrase, tags=set(item_cfg.tags)))
    clue = world.add(Entity(id="clue", type="clue", label="clue", phrase="a clue"))

    seeker.attrs["name"] = seeker_name
    friend.attrs["name"] = friend_name
    parent.attrs["name"] = parent.label_word

    world.para()
    introduce(world, place, seeker, friend, parent)
    world.para()
    set_quest(world, item_cfg, seeker, friend)
    first_guess(world, seeker, friend, trait, item_cfg)
    world.para()
    find_clue(world, cause, seeker, friend)
    follow_quest(world, cause, place, seeker, friend)
    reveal_item(world, cause, seeker, friend, item_cfg)
    world.para()
    apology_or_praise(world, seeker, friend, trait)
    ending(world, place, item_cfg, seeker, friend, parent)

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        cause=cause,
        seeker=seeker,
        friend=friend,
        parent=parent,
        locker=locker,
        item=item,
        clue=clue,
        outcome=outcome_of(StoryParams(
            place=place.id,
            item=item_cfg.id,
            cause=cause.id,
            seeker_name=seeker_name,
            seeker_type=seeker_type,
            friend_name=friend_name,
            friend_type=friend_type,
            parent_type=parent_type,
            trait=trait,
            seed=None,
        )),
        blamed=seeker.memes["blame"] >= THRESHOLD,
        hurt=friend.memes["hurt"] >= THRESHOLD,
        clue_found=clue.meters["found"] >= THRESHOLD,
        solved=item.meters["found"] >= THRESHOLD,
        moral="Do not blame before you know. Follow clues, tell the truth, and mend quick words.",
        seeker_name=seeker_name,
        friend_name=friend_name,
    )
    return world


PLACES = {
    "moon_dome": Place(
        id="moon_dome",
        label="the Moon-Milk Hall",
        intro="There stood a painted locker by the wall, blue as a plum and small as a stall.",
        dome_line="Light dripped through the glass in silver loaves and sleepy stars.",
        closing_image="{seeker} and {friend} skipped in a ring beneath the dome, while the {item} chimed the kindness song all the way home.",
        flags={"windy", "high_shelf"},
        tags={"dome", "locker"},
    ),
    "garden_dome": Place(
        id="garden_dome",
        label="the Garden Glass Room",
        intro="There stood a tidy locker beside the fern, with brass that gleamed at every turn.",
        dome_line="Vines tapped the shining dome as if the leaves knew every tune.",
        closing_image="{seeker} and {friend} danced by the beans and bloom, with the {item} bright in the sweet green room.",
        flags={"windy", "cozy"},
        tags={"dome", "garden"},
    ),
    "story_dome": Place(
        id="story_dome",
        label="the Story Shell House",
        intro="There stood a warm locker by the rug, with painted moons and a rabbit snug.",
        dome_line="The almighty dome above it curved like a pearl over a whispered tale.",
        closing_image="{seeker} and {friend} sat by the rug in gentle cheer, and the {item} made the ending clear.",
        flags={"cozy", "high_shelf"},
        tags={"dome", "story"},
    ),
}

ITEMS = {
    "map": MissingItem(
        id="map",
        label="map",
        phrase="the paper map with the gold star path",
        needed_for="the kindness march around the dome",
        clue_word="flutter",
        shape_tags={"flat"},
        tags={"fluttery", "paper", "map"},
    ),
    "bell": MissingItem(
        id="bell",
        label="bell",
        phrase="the little bell with the honey sound",
        needed_for="the closing ring of the kindness song",
        clue_word="jingle",
        shape_tags={"round"},
        tags={"rolling", "jingly", "bell"},
    ),
    "ribbon": MissingItem(
        id="ribbon",
        label="ribbon",
        phrase="the blue ribbon for the wishing wand",
        needed_for="the kindness wand dance",
        clue_word="twist",
        shape_tags={"soft"},
        tags={"fluttery", "stringy", "ribbon"},
    ),
}

CAUSES = {
    "breeze": Cause(
        id="breeze",
        label="breeze",
        rhyme_line="A window-breeze can whisk a light thing free.",
        clue_text="a little flutter of paper by the window latch",
        spot="the window ledge",
        reveal_text="Up on the window ledge lay the {item}, folded by the breeze as neatly as a note.",
        needs_place_flags={"windy"},
        needs_item_tags={"fluttery"},
        tags={"wind", "clue"},
    ),
    "bounce": Cause(
        id="bounce",
        label="bounce",
        rhyme_line="A round thing can hop where no small eye first looks.",
        clue_text="a tiny shining nick on the locker door, as if something had pinged away",
        spot="the top of the locker",
        reveal_text="High on the top of the locker sat the {item}, where it had bounced and come to rest.",
        needs_place_flags={"high_shelf"},
        needs_item_tags={"rolling"},
        tags={"bounce", "clue"},
    ),
    "kitten": Cause(
        id="kitten",
        label="kitten",
        rhyme_line="A soft paw sometimes borrows what jingles or trails.",
        clue_text="three soft pawprints near the cushion basket",
        spot="the cushion basket",
        reveal_text="Inside the cushion basket curled the {item}, tucked there by a sleepy kitten with a milk-white nose.",
        needs_place_flags={"cozy"},
        needs_item_tags={"jingly"},
        tags={"kitten", "clue"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Tess", "Nora", "Poppy", "Mabel", "Ivy", "June"]
BOY_NAMES = ["Toby", "Ned", "Ollie", "Benji", "Milo", "Finn", "Theo", "Robin"]
TRAITS = ["patient", "gentle", "careful", "truthful", "hasty", "proud", "fussy", "quick"]
PARENTS = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    item: str
    cause: str
    seeker_name: str
    seeker_type: str
    friend_name: str
    friend_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="moon_dome",
        item="map",
        cause="breeze",
        seeker_name="Mina",
        seeker_type="girl",
        friend_name="Toby",
        friend_type="boy",
        parent_type="mother",
        trait="patient",
        seed=None,
    ),
    StoryParams(
        place="story_dome",
        item="bell",
        cause="bounce",
        seeker_name="Nora",
        seeker_type="girl",
        friend_name="Milo",
        friend_type="boy",
        parent_type="father",
        trait="hasty",
        seed=None,
    ),
    StoryParams(
        place="garden_dome",
        item="bell",
        cause="kitten",
        seeker_name="Lulu",
        seeker_type="girl",
        friend_name="Finn",
        friend_type="boy",
        parent_type="mother",
        trait="gentle",
        seed=None,
    ),
    StoryParams(
        place="garden_dome",
        item="ribbon",
        cause="breeze",
        seeker_name="Poppy",
        seeker_type="girl",
        friend_name="Robin",
        friend_type="boy",
        parent_type="father",
        trait="quick",
        seed=None,
    ),
]


KNOWLEDGE = {
    "locker": [
        (
            "What is a locker?",
            "A locker is a small cupboard or cabinet where people keep their things safe and tidy."
        )
    ],
    "dome": [
        (
            "What is a dome?",
            "A dome is a roof shaped like half a ball. It curves over a room like a big round shell."
        )
    ],
    "wind": [
        (
            "How can wind move light things?",
            "Wind can push light things like paper and ribbon because they do not weigh very much. A small breeze can slide them or lift their edges."
        )
    ],
    "bounce": [
        (
            "Why can a bell bounce to a high place?",
            "A small round thing can ping off a hard surface and land somewhere unexpected. That is why people look high and low when they lose one."
        )
    ],
    "kitten": [
        (
            "Why might a kitten carry or hide a little thing?",
            "Kittens like to bat at small jangly objects and drag them to cozy places. They are playing, not trying to be mean."
        )
    ],
    "truth": [
        (
            "Why is it good to tell the truth after a mistake?",
            "Truth helps people understand what really happened. It makes it easier to fix the problem and trust each other again."
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology shows that you know your quick words or actions hurt someone. It helps mend feelings when it is honest and kind."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you solve a mystery. It points your thinking in the right direction."
        )
    ],
}
KNOWLEDGE_ORDER = ["locker", "dome", "clue", "wind", "bounce", "kitten", "truth", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    item = f["item_cfg"]
    return [
        f'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the words "locker", "almighty", and "dome". Make it a mystery to solve.',
        f"Tell a gentle quest story where two children discover that the {item.label} is missing from a locker in {place.label}, and they solve the mystery with clues.",
        "Write a small moral tale in rhyme where a child learns not to blame too quickly, and the ending proves that truth and kindness matter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    friend = f["friend"]
    parent = f["parent"]
    item = f["item_cfg"]
    cause = f["cause"]
    place = f["place"]

    seeker_name = seeker.label
    friend_name = friend.label
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker_name} and {friend_name}, two children in {place.label}. They were trying to find a missing {item.label} from the locker."
        ),
        (
            f"Why was finding the {item.label} important?",
            f"They needed the {item.label} for {item.needed_for}. That missing object turned the morning into a little quest."
        ),
        (
            "What clue helped them solve the mystery?",
            f"They found {cause.clue_text}. The clue pointed them toward {cause.spot} and showed that the thing was misplaced, not stolen."
        ),
    ]

    if f.get("blamed"):
        qa.append(
            (
                f"How did {seeker_name} make a mistake, and how was it fixed?",
                f"{seeker_name} guessed too quickly and asked if {friend_name} had taken the {item.label}. After the clue was found, {seeker_name} understood the mistake, apologized, and used honest words to mend the hurt."
            )
        )
    else:
        qa.append(
            (
                f"How did {seeker_name} help solve the mystery kindly?",
                f"{seeker_name} chose not to blame anyone before looking for evidence. That patience left room for {friend_name} to notice the clue and help solve the mystery."
            )
        )

    qa.append(
        (
            "What is the moral of the story?",
            f"The story teaches that you should not blame before you know the truth. Careful eyes, kind words, and a true apology make a better ending."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They found the {item.label}, brought it back from {cause.spot}, and used it for {item.needed_for}. Under the almighty dome, the children ended in song and peace while {pw} praised truth and kindness."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"locker", "dome", "clue", "truth"}
    if f.get("blamed"):
        tags.add("apology")
    tags |= set(f["cause"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, item: MissingItem, cause: Cause) -> str:
    want_place = ", ".join(sorted(cause.needs_place_flags)) or "no special place feature"
    want_item = ", ".join(sorted(cause.needs_item_tags)) or "no special item feature"
    return (
        f"(No story: {cause.label} does not fit this setup. "
        f"It needs a place with {want_place} and an item with {want_item}, "
        f"but {place.label} and the {item.label} do not match that mystery.)"
    )


ASP_RULES = r"""
valid(P, I, C) :- place(P), item(I), cause(C), fits_place(P, C), fits_item(I, C).

fits_place(P, C) :- cause(C), place(P), not needs_place(P, C).
fits_item(I, C)  :- cause(C), item(I), not needs_item(I, C).

needs_place(P, C) :- cause_needs_place_flag(C, F), not place_has_flag(P, F).
needs_item(I, C)  :- cause_needs_item_tag(C, T), not item_has_tag(I, T).

calm_trait(T) :- trait(T), is_calm(T).
outcome(gentle) :- chosen_trait(T), calm_trait(T).
outcome(sting)  :- chosen_trait(T), not calm_trait(T).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for flag in sorted(place.flags):
            lines.append(asp.fact("place_has_flag", place_id, flag))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_has_tag", item_id, tag))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for flag in sorted(cause.needs_place_flags):
            lines.append(asp.fact("cause_needs_place_flag", cause_id, flag))
        for tag in sorted(cause.needs_item_tags):
            lines.append(asp.fact("cause_needs_item_tag", cause_id, tag))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("is_calm", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "locker" not in sample.story or "dome" not in sample.story or "almighty" not in sample.story:
        raise StoryError("Smoke test failed: required seed words were not present in the story.")


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
        params.seed = seed
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
        _smoke_generate()
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme mystery storyworld: a missing thing in a locker beneath an almighty dome."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--seeker-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--seeker-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mystery setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, forced_type: Optional[str], avoid: str = "") -> tuple[str, str]:
    person_type = forced_type or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if person_type == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), person_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.cause:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        cause = CAUSES[args.cause]
        if not valid_combo(place, item, cause):
            raise StoryError(explain_rejection(place, item, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, cause_id = rng.choice(sorted(combos))
    seeker_name, seeker_type = _pick_name(rng, args.seeker_type)
    friend_name, friend_type = _pick_name(rng, args.friend_type, avoid=seeker_name)
    if args.seeker_name:
        seeker_name = args.seeker_name
    if args.friend_name:
        friend_name = args.friend_name
    trait = args.trait or rng.choice(TRAITS)
    parent_type = args.parent or rng.choice(PARENTS)
    return StoryParams(
        place=place_id,
        item=item_id,
        cause=cause_id,
        seeker_name=seeker_name,
        seeker_type=seeker_type,
        friend_name=friend_name,
        friend_type=friend_type,
        parent_type=parent_type,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Invalid item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Invalid trait: {params.trait})")
    if params.parent_type not in PARENTS:
        raise StoryError(f"(Invalid parent: {params.parent_type})")

    place = PLACES[params.place]
    item = ITEMS[params.item]
    cause = CAUSES[params.cause]
    if not valid_combo(place, item, cause):
        raise StoryError(explain_rejection(place, item, cause))

    world = tell(
        place=place,
        item_cfg=item,
        cause=cause,
        seeker_name=params.seeker_name,
        seeker_type=params.seeker_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        parent_type=params.parent_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, cause) combos:\n")
        for place, item, cause in combos:
            print(f"  {place:11} {item:7} {cause}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.seeker_name} & {p.friend_name}: {p.item} in {p.place} ({p.cause}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
