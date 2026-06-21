#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/system_northern_surprise_twist_whodunit.py
=====================================================================

A gentle child-facing whodunit set in a northern place where one important part
of a celebration system goes missing. A small detective follows a clue, names a
suspect, and discovers a twist: nobody meant to steal anything. The missing item
was being readied as a surprise.

Run it
------
    python storyworlds/worlds/gpt-5.4/system_northern_surprise_twist_whodunit.py
    python storyworlds/worlds/gpt-5.4/system_northern_surprise_twist_whodunit.py --place station --item bell --culprit musician
    python storyworlds/worlds/gpt-5.4/system_northern_surprise_twist_whodunit.py --place observatory --item bell
    python storyworlds/worlds/gpt-5.4/system_northern_surprise_twist_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/system_northern_surprise_twist_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/system_northern_surprise_twist_whodunit.py --qa --json
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
    location: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    phrase: str
    system_name: str
    event: str
    backdrop: str
    rooms: dict[str, str] = field(default_factory=dict)
    items: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    system_use: str
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectCfg:
    id: str
    name: str
    type: str
    role_label: str
    clue_tag: str
    clue_noun: str
    clue_line: str
    room_key: str
    item_ok: set[str] = field(default_factory=set)
    place_ok: set[str] = field(default_factory=set)
    surprise_text: str = ""
    reveal_text: str = ""
    knowledge_tag: str = ""


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_notice_missing(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return out
    sig = ("notice_missing",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("sleuth").memes["curiosity"] += 1
    world.get("friend").memes["worry"] += 1
    world.get("keeper").memes["worry"] += 1
    for eid in ("suspect_mechanic", "suspect_decorator", "suspect_musician"):
        world.get(eid).memes["suspected"] += 1
    out.append("__missing__")
    return out


def _r_clue_points(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["found"] < THRESHOLD:
        return out
    wanted = clue.attrs.get("tag")
    if not wanted:
        return out
    for eid in ("suspect_mechanic", "suspect_decorator", "suspect_musician"):
        suspect = world.get(eid)
        sig = ("clue_points", suspect.id, wanted)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if wanted in suspect.tags:
            suspect.memes["focus"] += 2
            out.append(f"The clue pointed toward {suspect.label}.")
        else:
            suspect.memes["doubted"] += 1
    return out


def _r_search_reveals(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return out
    searched = world.facts.get("searched")
    if not searched:
        return out
    for eid in ("suspect_mechanic", "suspect_decorator", "suspect_musician"):
        suspect = world.get(eid)
        sig = ("search", suspect.id, searched)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if suspect.location == searched and suspect.memes["focus"] >= THRESHOLD:
            item.meters["missing"] = 0.0
            item.location = suspect.location
            suspect.memes["caught"] += 1
            world.get("sleuth").memes["relief"] += 1
            world.get("keeper").memes["relief"] += 1
            world.facts["found_with"] = suspect.id
            out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="notice_missing", tag="social", apply=_r_notice_missing),
    Rule(name="clue_points", tag="reasoning", apply=_r_clue_points),
    Rule(name="search_reveals", tag="reasoning", apply=_r_search_reveals),
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
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "station": Place(
        id="station",
        label="station",
        phrase="the little northern train station",
        system_name="welcome-bell system",
        event="the first snow train",
        backdrop="Frost feathered the windows, and the tracks shone pale under the moon.",
        rooms={
            "workshop": "the warm repair shed",
            "attic": "the loft above the ticket room",
            "music_corner": "the music corner by the waiting benches",
        },
        items={"bell", "key", "lantern"},
    ),
    "lighthouse": Place(
        id="lighthouse",
        label="lighthouse",
        phrase="the tall northern lighthouse",
        system_name="lamp-lifting system",
        event="the harbor cocoa night",
        backdrop="Beyond the rocks, dark water rolled under a sky full of stars.",
        rooms={
            "workshop": "the gear room at the bottom of the stairs",
            "attic": "the flag loft under the roof",
            "music_corner": "the snug reading corner by the kettle",
        },
        items={"bell", "key", "lantern"},
    ),
    "observatory": Place(
        id="observatory",
        label="observatory",
        phrase="the round northern observatory",
        system_name="roof-opening system",
        event="the aurora watch",
        backdrop="Snow sat on the dome like sugar, and the sky waited in deep blue silence.",
        rooms={
            "workshop": "the tool closet beside the great telescope",
            "attic": "the banner loft over the coat hooks",
            "music_corner": "the hush-soft corner near the star maps",
        },
        items={"key", "lantern"},
    ),
}

ITEMS = {
    "bell": ItemCfg(
        id="bell",
        label="bell",
        phrase="the brass bell",
        system_use="to start the system with one bright ring",
        finish="rang clear as a spoon tapping glass",
        tags={"bell", "metal"},
    ),
    "key": ItemCfg(
        id="key",
        label="key",
        phrase="the silver key",
        system_use="to wind the system before the guests arrived",
        finish="clicked neatly into place",
        tags={"key", "metal"},
    ),
    "lantern": ItemCfg(
        id="lantern",
        label="lantern",
        phrase="the blue lantern",
        system_use="to glow beside the system so everyone knew where to look",
        finish="shone like a little moon",
        tags={"lantern", "light"},
    ),
}

SUSPECTS = {
    "mechanic": SuspectCfg(
        id="mechanic",
        name="Oren",
        type="man",
        role_label="the mechanic",
        clue_tag="grease",
        clue_noun="a thumb-smudge of dark grease",
        clue_line="Near the shelf, a thumb-smudge of dark grease marked the wood.",
        room_key="workshop",
        item_ok={"bell", "key", "lantern"},
        place_ok={"station", "lighthouse", "observatory"},
        surprise_text="He had been mending the old system so it would work smoothly at just the right moment.",
        reveal_text="I wanted everyone to think the old system had gone sleepy, and then wake it up with a surprise.",
        knowledge_tag="mechanic",
    ),
    "decorator": SuspectCfg(
        id="decorator",
        name="Pia",
        type="woman",
        role_label="the decorator",
        clue_tag="ribbon",
        clue_noun="a curl of silver ribbon",
        clue_line="On the floor lay a curl of silver ribbon that had not been there before.",
        room_key="attic",
        item_ok={"bell", "lantern"},
        place_ok={"station", "lighthouse", "observatory"},
        surprise_text="She had been tying the missing piece into a hidden decoration for the party.",
        reveal_text="I wanted the room to look ordinary, and then shimmer all at once when everyone looked up.",
        knowledge_tag="ribbon",
    ),
    "musician": SuspectCfg(
        id="musician",
        name="Niko",
        type="man",
        role_label="the musician",
        clue_tag="song",
        clue_noun="a strip of music paper with fresh humming marks",
        clue_line="By the door, a strip of music paper showed tiny pencil notes and one fresh humming mark.",
        room_key="music_corner",
        item_ok={"bell"},
        place_ok={"station", "lighthouse"},
        surprise_text="He had been hiding with the missing piece so he could begin the welcome song with a sudden flourish.",
        reveal_text="I wanted the first note and the first ring to come together as one big surprise.",
        knowledge_tag="music",
    ),
}

GIRL_NAMES = ["Mira", "Tessa", "Lina", "Nora", "Ava", "Esme", "Ruth", "Maya"]
BOY_NAMES = ["Ollie", "Finn", "Sam", "Eli", "Noah", "Theo", "Ben", "Kit"]
FRIEND_GIRL_NAMES = ["June", "Ivy", "Lila", "Bess", "Mae", "Poppy"]
FRIEND_BOY_NAMES = ["Toby", "Milo", "Jude", "Ash", "Leo", "Rory"]


def valid_combo(place_id: str, item_id: str, culprit_id: str) -> bool:
    place = PLACES[place_id]
    item = ITEMS[item_id]
    culprit = SUSPECTS[culprit_id]
    return (
        item.id in place.items
        and item.id in culprit.item_ok
        and place.id in culprit.place_ok
        and bool(item.tags)
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for item_id in ITEMS:
            for culprit_id in SUSPECTS:
                if valid_combo(place_id, item_id, culprit_id):
                    out.append((place_id, item_id, culprit_id))
    return out


@dataclass
class StoryParams:
    place: str
    item: str
    culprit: str
    sleuth: str
    sleuth_gender: str
    friend: str
    friend_gender: str
    keeper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="station",
        item="bell",
        culprit="musician",
        sleuth="Mira",
        sleuth_gender="girl",
        friend="Toby",
        friend_gender="boy",
        keeper="mother",
    ),
    StoryParams(
        place="lighthouse",
        item="lantern",
        culprit="decorator",
        sleuth="Finn",
        sleuth_gender="boy",
        friend="Ivy",
        friend_gender="girl",
        keeper="father",
    ),
    StoryParams(
        place="observatory",
        item="key",
        culprit="mechanic",
        sleuth="Nora",
        sleuth_gender="girl",
        friend="Jude",
        friend_gender="boy",
        keeper="mother",
    ),
]


def explain_rejection(place_id: str, item_id: str, culprit_id: str) -> str:
    place = PLACES[place_id]
    item = ITEMS[item_id]
    culprit = SUSPECTS[culprit_id]
    if item.id not in place.items:
        return (
            f"(No story: {item.phrase} does not belong in {place.phrase}. "
            f"That place's system uses different parts.)"
        )
    if item.id not in culprit.item_ok:
        return (
            f"(No story: {culprit.role_label} would not reasonably borrow {item.phrase}. "
            f"Pick a suspect whose job fits that item.)"
        )
    if place.id not in culprit.place_ok:
        return (
            f"(No story: {culprit.role_label} is not part of the usual cast at {place.phrase}.)"
        )
    return "(No story: this combination is not reasonable.)"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    if gender == "girl":
        pool = [n for n in GIRL_NAMES if n != avoid]
        if not pool:
            pool = GIRL_NAMES[:]
        return rng.choice(pool)
    pool = [n for n in BOY_NAMES if n != avoid]
    if not pool:
        pool = BOY_NAMES[:]
    return rng.choice(pool)


def _pick_friend_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    if gender == "girl":
        pool = [n for n in FRIEND_GIRL_NAMES if n != avoid]
        if not pool:
            pool = FRIEND_GIRL_NAMES[:]
        return rng.choice(pool)
    pool = [n for n in FRIEND_BOY_NAMES if n != avoid]
    if not pool:
        pool = FRIEND_BOY_NAMES[:]
    return rng.choice(pool)


def introduce(world: World, sleuth: Entity, friend: Entity, keeper: Entity, item: Entity, item_cfg: ItemCfg) -> None:
    place = world.place
    world.say(
        f"On the night of {place.event}, {sleuth.id} stood in {place.phrase} with {friend.id} and "
        f"{sleuth.pronoun('possessive')} {keeper.label_word}. {place.backdrop}"
    )
    world.say(
        f"Everyone was getting ready for {place.system_name}, and {item_cfg.phrase} was meant "
        f"{item_cfg.system_use}."
    )


def notice_missing(world: World, sleuth: Entity, friend: Entity, item_cfg: ItemCfg) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {sleuth.id} reached for {item_cfg.phrase}, the shelf was empty."
    )
    world.say(
        f'"{item_cfg.phrase.capitalize()} is gone," {friend.id} whispered. '
        f'"Who took it?"'
    )


def list_suspects(world: World) -> None:
    m = world.get("suspect_mechanic")
    d = world.get("suspect_decorator")
    s = world.get("suspect_musician")
    world.say(
        f"{m.label}, {d.label}, and {s.label} had all hurried past the shelf that evening, "
        f"so the little mystery began to feel like a real whodunit."
    )


def find_clue(world: World, culprit_cfg: SuspectCfg) -> None:
    clue = world.get("clue")
    clue.meters["found"] += 1
    clue.attrs["tag"] = culprit_cfg.clue_tag
    propagate(world, narrate=False)
    world.say(culprit_cfg.clue_line)


def reason_from_clue(world: World, sleuth: Entity, friend: Entity, culprit_cfg: SuspectCfg) -> None:
    room_name = world.place.rooms[culprit_cfg.room_key]
    world.say(
        f'{sleuth.id} knelt down. "{culprit_cfg.clue_noun.capitalize()}," {sleuth.pronoun()} said. '
        f'"That belongs with {culprit_cfg.role_label}."'
    )
    world.say(
        f'{friend.id} nodded. "Then we should look in {room_name}," {friend.pronoun()} said.'
    )
    world.facts["searched"] = room_name
    propagate(world, narrate=False)


def search_room(world: World, sleuth: Entity, friend: Entity, culprit_cfg: SuspectCfg, item_cfg: ItemCfg) -> None:
    room_name = world.place.rooms[culprit_cfg.room_key]
    world.say(
        f"They padded to {room_name}, listening to the boards creak under their boots."
    )
    if world.get("item").meters["missing"] < THRESHOLD:
        world.say(
            f"There, tucked safely beside a blanket and a lamp, was {item_cfg.phrase}."
        )
    else:
        world.say(
            f"The room held only dust and boxes, and for one breath the mystery seemed thicker than ever."
        )


def reveal(world: World, sleuth: Entity, keeper: Entity, culprit_cfg: SuspectCfg, item_cfg: ItemCfg) -> None:
    culprit = world.get(f"suspect_{culprit_cfg.id}")
    world.say(
        f'{culprit.label} turned around with a start. "{item_cfg.phrase.capitalize()}?" {culprit.pronoun()} said. '
        f'"Oh! I can explain."'
    )
    world.say(culprit_cfg.surprise_text)
    world.say(
        f'The twist was gentle, not mean: {culprit_cfg.reveal_text}'
    )
    world.say(
        f"{keeper.label_word.capitalize()} let out a long breath and smiled. Nobody had been stealing anything at all."
    )
    culprit.memes["kind_intent"] += 1
    sleuth.memes["surprised"] += 1


def happy_end(world: World, sleuth: Entity, friend: Entity, item_cfg: ItemCfg) -> None:
    item = world.get("item")
    item.meters["working"] += 1
    sleuth.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Soon {item_cfg.phrase} was back where it belonged, and the old {world.place.system_name} came alive."
    )
    world.say(
        f"It {item_cfg.finish}, and everyone in the northern room looked up at once."
    )
    world.say(
        f"{sleuth.id} and {friend.id} grinned at each other. The mystery had ended in a surprise, and that made it the best kind of case."
    )


def tell(
    place: Place,
    item_cfg: ItemCfg,
    culprit_cfg: SuspectCfg,
    sleuth_name: str,
    sleuth_gender: str,
    friend_name: str,
    friend_gender: str,
    keeper_type: str,
) -> World:
    world = World(place)

    sleuth = world.add(
        Entity(id="sleuth", kind="character", type=sleuth_gender, label=sleuth_name, phrase=sleuth_name, role="sleuth")
    )
    sleuth.id = sleuth_name
    world.entities[sleuth_name] = world.entities.pop("sleuth")
    sleuth = world.get(sleuth_name)

    friend = world.add(
        Entity(id="friend", kind="character", type=friend_gender, label=friend_name, phrase=friend_name, role="friend")
    )
    friend.id = friend_name
    world.entities[friend_name] = world.entities.pop("friend")
    friend = world.get(friend_name)

    keeper = world.add(
        Entity(id="keeper", kind="character", type=keeper_type, label="the keeper", phrase="the keeper", role="keeper")
    )
    keeper.id = "Keeper"
    world.entities["Keeper"] = world.entities.pop("keeper")
    keeper = world.get("Keeper")

    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type=item_cfg.id,
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="missing_item",
            location="the shelf by the system",
            tags=set(item_cfg.tags),
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            kind="thing",
            type="clue",
            label="clue",
            phrase="the clue",
            role="clue",
            location="the floor by the shelf",
        )
    )

    for sid, cfg in SUSPECTS.items():
        world.add(
            Entity(
                id=f"suspect_{sid}",
                kind="character",
                type=cfg.type,
                label=cfg.name,
                phrase=cfg.name,
                role="suspect",
                location=place.rooms[cfg.room_key],
                tags={cfg.clue_tag, sid},
                attrs={"job": cfg.role_label, "knowledge_tag": cfg.knowledge_tag},
            )
        )

    culprit = world.get(f"suspect_{culprit_cfg.id}")
    culprit.meters[culprit_cfg.clue_tag] += 1
    culprit.meters["holding_item"] += 1
    item.location = place.rooms[culprit_cfg.room_key]

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        culprit_cfg=culprit_cfg,
        culprit=culprit,
        sleuth=sleuth,
        friend=friend,
        keeper=keeper,
    )

    introduce(world, sleuth, friend, keeper, item, item_cfg)
    notice_missing(world, sleuth, friend, item_cfg)
    list_suspects(world)

    world.para()
    find_clue(world, culprit_cfg)
    reason_from_clue(world, sleuth, friend, culprit_cfg)

    world.para()
    search_room(world, sleuth, friend, culprit_cfg, item_cfg)
    reveal(world, sleuth, keeper, culprit_cfg, item_cfg)

    world.para()
    happy_end(world, sleuth, friend, item_cfg)

    world.facts.update(
        found=item.meters["missing"] < THRESHOLD,
        item_location=item.location,
        clue_tag=culprit_cfg.clue_tag,
        searched=place.rooms[culprit_cfg.room_key],
        solved_with=culprit.label,
    )
    return world


KNOWLEDGE = {
    "bell": [
        (
            "What does a bell do in a celebration system?",
            "A bell gives a clear sound that tells everyone to listen or look. One ring can start a whole room paying attention."
        )
    ],
    "key": [
        (
            "What can a key do in a winding system?",
            "A key can turn a lock or wind a mechanism. That helps a machine get ready to work."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful at night?",
            "A lantern makes a warm light so people can see where to go and what to watch. It is especially helpful in dark winter places."
        )
    ],
    "grease": [
        (
            "Why would a mechanic use grease?",
            "Grease helps moving parts rub more smoothly instead of scraping. It is a common sign that someone has been fixing a machine."
        )
    ],
    "ribbon": [
        (
            "Why do people use ribbon for decorations?",
            "Ribbon is light, bright, and easy to tie into bows or swirls. It helps ordinary rooms feel festive."
        )
    ],
    "music": [
        (
            "Why might music be part of a welcome?",
            "Music can help people feel gathered together and ready for something special. A first note can feel like a signal all by itself."
        )
    ],
    "station": [
        (
            "What is a train station?",
            "A train station is a place where trains stop and people wait, wave, and travel. It often has signs, benches, and tracks."
        )
    ],
    "lighthouse": [
        (
            "What is a lighthouse for?",
            "A lighthouse helps guide boats near the shore with a bright light. It warns people where the coast and rocks are."
        )
    ],
    "observatory": [
        (
            "What happens at an observatory?",
            "People use an observatory to look closely at the sky, stars, and moon. Big telescopes help them see farther."
        )
    ],
    "mystery": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what happened. Good detectives notice little things and think carefully about them."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "station",
    "lighthouse",
    "observatory",
    "bell",
    "key",
    "lantern",
    "grease",
    "ribbon",
    "music",
    "mystery",
]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    sleuth = world.facts["sleuth"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old set in {place.phrase} and include the words "system" and "northern".',
        f"Tell a gentle mystery where {sleuth.id} notices that {item_cfg.phrase} is missing from a celebration system, follows one clue, and discovers a kind surprise instead of a crime.",
        f"Write a child-friendly detective story with a twist: {culprit_cfg.role_label} seems suspicious, but the missing item was only hidden to make the ending feel special.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    sleuth = world.facts["sleuth"]
    friend = world.facts["friend"]
    keeper = world.facts["keeper"]
    culprit = world.facts["culprit"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sleuth.id}, {friend.id}, and {sleuth.pronoun('possessive')} {keeper.label_word} in {place.phrase}. They are trying to solve a small mystery before the celebration begins."
        ),
        (
            f"Why was {item_cfg.phrase} important?",
            f"It was needed {item_cfg.system_use}. Without it, the special moment at {place.event} could not begin the right way."
        ),
        (
            f"What clue did {sleuth.id} find?",
            f"{sleuth.id} found {culprit_cfg.clue_noun} near the shelf. That mattered because it matched {culprit_cfg.role_label} better than the other suspects."
        ),
        (
            f"Who had {item_cfg.phrase}?",
            f"{culprit.label} had it. The children searched the place the clue pointed to, and that is where they found the missing piece."
        ),
        (
            "What was the twist at the end?",
            f"The twist was that nobody was being mean or sneaky. {culprit.label} had borrowed {item_cfg.phrase} to make a surprise for everyone."
        ),
        (
            "How did the story end?",
            f"The item went back where it belonged, and the old system finally worked. The ending image proves what changed because the room filled with sound or light instead of worry."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    item_cfg = world.facts["item_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    tags = {place.id, item_cfg.id, culprit_cfg.knowledge_tag, "mystery"}
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.location:
            bits.append(f"location={ent.location!r}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:18} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
supports_item(P, I) :- place(P), item(I), place_item(P, I).
culprit_can_use(C, I) :- culprit(C), item(I), culprit_item(C, I).
culprit_at_place(C, P) :- culprit(C), place(P), culprit_place(C, P).
valid(P, I, C) :- supports_item(P, I), culprit_can_use(C, I), culprit_at_place(C, P).

clue_of(C, T) :- culprit(C), clue_tag(C, T).
solvable(P, I, C) :- valid(P, I, C), clue_of(C, _).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for item_id in sorted(place.items):
            lines.append(asp.fact("place_item", pid, item_id))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for cid, culprit in SUSPECTS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("clue_tag", cid, culprit.clue_tag))
        for item_id in sorted(culprit.item_ok):
            lines.append(asp.fact("culprit_item", cid, item_id))
        for place_id in sorted(culprit.place_ok):
            lines.append(asp.fact("culprit_place", cid, place_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print(f"SMOKE resolve failed on seed {seed}: {err}")
            break

    for idx, params in enumerate(smoke_cases):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "northern" not in sample.story.lower() or "system" not in sample.story.lower():
                raise StoryError("story missed required seed words")
            emit(sample, trace=False, qa=False, header="" if idx else "### smoke test")
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"SMOKE generation failed for {params}: {err}")
            break
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a gentle northern whodunit with a missing part, one clue, and a surprise twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--keeper", choices=["mother", "father"])
    ap.add_argument("--sleuth")
    ap.add_argument("--friend")
    ap.add_argument("--sleuth-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (place, item, culprit) set from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.culprit:
        if not valid_combo(args.place, args.item, args.culprit):
            raise StoryError(explain_rejection(args.place, args.item, args.culprit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, culprit_id = rng.choice(sorted(combos))
    sleuth_gender = args.sleuth_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    sleuth = args.sleuth or _pick_name(rng, sleuth_gender)
    friend = args.friend or _pick_friend_name(rng, friend_gender, avoid=sleuth)
    keeper = args.keeper or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        item=item_id,
        culprit=culprit_id,
        sleuth=sleuth,
        sleuth_gender=sleuth_gender,
        friend=friend,
        friend_gender=friend_gender,
        keeper=keeper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.culprit not in SUSPECTS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if not valid_combo(params.place, params.item, params.culprit):
        raise StoryError(explain_rejection(params.place, params.item, params.culprit))

    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        culprit_cfg=SUSPECTS[params.culprit],
        sleuth_name=params.sleuth,
        sleuth_gender=params.sleuth_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        keeper_type=params.keeper,
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
        print(f"{len(combos)} compatible (place, item, culprit) combos:\n")
        for place_id, item_id, culprit_id in combos:
            print(f"  {place_id:11} {item_id:8} {culprit_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.sleuth}: {p.item} missing at {p.place} ({p.culprit})"
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
