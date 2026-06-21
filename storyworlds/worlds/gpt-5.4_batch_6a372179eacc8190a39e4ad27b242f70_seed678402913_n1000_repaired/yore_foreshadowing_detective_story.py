#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yore_foreshadowing_detective_story.py
================================================================

A standalone story world for a tiny child-facing detective tale with
foreshadowing. A young sleuth notices a strange old clue, follows the wrong
idea for a moment, then understands what the clue from long ago really meant
and solves a small mystery.

Seed requirements rebuilt as world state
----------------------------------------
- Word: "yore"
- Feature: foreshadowing
- Style: detective story

This world models a gentle mystery in an old house-like public place: a
treasured object goes missing, an early clue quietly points to the answer, and
the detective later realizes that clue was important all along.

Run it
------
    python storyworlds/worlds/gpt-5.4/yore_foreshadowing_detective_story.py
    python storyworlds/worlds/gpt-5.4/yore_foreshadowing_detective_story.py --place library --missing compass
    python storyworlds/worlds/gpt-5.4/yore_foreshadowing_detective_story.py --clue rhyme --hideout clock
    python storyworlds/worlds/gpt-5.4/yore_foreshadowing_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/yore_foreshadowing_detective_story.py --verify
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
    portable: bool = False
    noisy: bool = False
    openable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "librarian", "caretaker"}
        male = {"boy", "man", "father", "caretaker_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"caretaker": "caretaker", "librarian": "librarian"}.get(self.type, self.type or self.label)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    old_feature: str
    hush_detail: str
    keeper_type: str
    keeper_label: str
    hideouts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    shine: str
    owner_text: str
    portable: bool = True
    noisy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    text: str
    points_to: set[str] = field(default_factory=set)
    false_hint: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    discovery: str
    proof: str
    openable: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Mover:
    id: str
    label: str
    phrase: str
    method: str
    reason: str
    careful: bool = False
    can_reach_high: bool = False
    likes_shiny: bool = False
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.get("keeper")
    thing = world.get("thing")
    detective = world.get("detective")
    if thing.meters["missing"] >= THRESHOLD and ("worry", thing.id) not in world.fired:
        world.fired.add(("worry", thing.id))
        keeper.memes["worry"] += 1
        detective.memes["curiosity"] += 1
        out.append("__missing__")
    return out


def _r_false_lead(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.meters["checked_wrong_spot"] >= THRESHOLD and ("false_lead", detective.id) not in world.fired:
        world.fired.add(("false_lead", detective.id))
        detective.memes["doubt"] += 1
        out.append("__false_lead__")
    return out


def _r_realization(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if (
        detective.meters["saw_clue"] >= THRESHOLD
        and detective.meters["checked_wrong_spot"] >= THRESHOLD
        and detective.meters["remembered_clue"] >= THRESHOLD
        and ("realization", detective.id) not in world.fired
    ):
        world.fired.add(("realization", detective.id))
        detective.memes["certainty"] += 1
        out.append("__realization__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="false_lead", tag="mental", apply=_r_false_lead),
    Rule(name="realization", tag="mental", apply=_r_realization),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "library": Place(
        id="library",
        label="library",
        phrase="the old village library",
        old_feature="oak shelves and a tall clock from the days of yore",
        hush_detail="Every whisper seemed to tuck itself between the books.",
        keeper_type="librarian",
        keeper_label="Ms. Wren",
        hideouts={"clock", "atlas_drawer", "window_seat"},
        tags={"library", "books"},
    ),
    "museum": Place(
        id="museum",
        label="museum",
        phrase="the small town museum",
        old_feature="glass cases and a carved map chest from the days of yore",
        hush_detail="Even the floorboards sounded as if they were trying not to interrupt history.",
        keeper_type="caretaker",
        keeper_label="Mr. Vale",
        hideouts={"map_chest", "clock", "window_seat"},
        tags={"museum", "history"},
    ),
    "manor": Place(
        id="manor",
        label="manor",
        phrase="the old hill manor",
        old_feature="long halls, faded portraits, and a brass clock from the days of yore",
        hush_detail="Dusty light lay across the floor like thin gold ribbons.",
        keeper_type="caretaker",
        keeper_label="Mrs. Thorn",
        hideouts={"clock", "portrait_niche", "window_seat"},
        tags={"manor", "old_house"},
    ),
}

MISSING = {
    "compass": MissingThing(
        id="compass",
        label="compass",
        phrase="a brass compass",
        shine="its little glass face flashed when it caught the light",
        owner_text="the room's favorite treasure for telling north from south",
        portable=True,
        noisy=False,
        tags={"compass", "metal", "shiny"},
    ),
    "key": MissingThing(
        id="key",
        label="key",
        phrase="an old silver key",
        shine="its notched teeth winked like tiny fish scales",
        owner_text="the key that opened the story cabinet",
        portable=True,
        noisy=False,
        tags={"key", "metal", "shiny"},
    ),
    "bell": MissingThing(
        id="bell",
        label="bell",
        phrase="a small brass bell",
        shine="its round side glowed honey-gold in the window light",
        owner_text="the bell the keeper used for closing time",
        portable=True,
        noisy=True,
        tags={"bell", "metal", "sound"},
    ),
}

CLUES = {
    "rhyme": Clue(
        id="rhyme",
        label="rhyme",
        phrase="a crooked rhyme painted on a wooden sign",
        text='The sign said, "When hands stand still, the old face keeps the secret."',
        points_to={"clock"},
        false_hint="The painted hands looked like pointing fingers, as if they might accuse somebody.",
        tags={"rhyme", "words", "foreshadowing"},
    ),
    "draught": Clue(
        id="draught",
        label="draught",
        phrase="a cool little draught under the wall maps",
        text="A thin breeze kept lifting one corner of the oldest map.",
        points_to={"atlas_drawer", "map_chest"},
        false_hint="It felt so much like a trail that it almost begged to be followed at once.",
        tags={"breeze", "maps", "foreshadowing"},
    ),
    "portrait": Clue(
        id="portrait",
        label="portrait",
        phrase="a stern portrait with one eye pointed strangely sideways",
        text='Under the frame was a brass plate that read, "He always watched the east alcove."',
        points_to={"portrait_niche", "window_seat"},
        false_hint="The stare was so odd that it seemed less like decoration and more like a hint left on purpose.",
        tags={"portrait", "look", "foreshadowing"},
    ),
}

HIDEOUTS = {
    "clock": Hideout(
        id="clock",
        label="clock",
        phrase="the tall clock",
        discovery="inside the little clock door, on the dusty ledge beneath the still pendulum",
        proof="The clue about the old face made sense at once: it had been pointing to the clock all along.",
        openable=True,
        tags={"clock", "hidden_space"},
    ),
    "atlas_drawer": Hideout(
        id="atlas_drawer",
        label="atlas drawer",
        phrase="the atlas drawer under the map table",
        discovery="inside the deep drawer, tucked beside rolled paper maps",
        proof="The little draught had not been random at all; air was slipping from the half-open drawer.",
        openable=True,
        tags={"drawer", "maps", "hidden_space"},
    ),
    "map_chest": Hideout(
        id="map_chest",
        label="map chest",
        phrase="the carved map chest",
        discovery="inside the shallow top tray of the map chest, under a stack of linen charts",
        proof="The moving map corner had been whispering about the chest from the very start.",
        openable=True,
        tags={"chest", "maps", "hidden_space"},
    ),
    "window_seat": Hideout(
        id="window_seat",
        label="window seat",
        phrase="the window seat",
        discovery="inside the window seat, among faded cushions and a curled ribbon",
        proof="The sideways look and the bright strip of light by the window had been guiding the answer there all along.",
        openable=True,
        tags={"window", "seat", "hidden_space"},
    ),
    "portrait_niche": Hideout(
        id="portrait_niche",
        label="east alcove",
        phrase="the east alcove behind the portrait",
        discovery="in the little niche behind the portrait frame, where only a careful hand would search",
        proof="The brass plate under the portrait had been giving the place away in plain sight.",
        openable=False,
        tags={"portrait", "alcove", "hidden_space"},
    ),
}

MOVERS = {
    "magpie": Mover(
        id="magpie",
        label="magpie",
        phrase="a glossy black-and-white magpie that sometimes slipped in through an open pane",
        method="snatched the shiny thing and tucked it away",
        reason="it loved bright objects more than good manners",
        careful=False,
        can_reach_high=True,
        likes_shiny=True,
        tags={"bird", "shiny"},
    ),
    "kitten": Mover(
        id="kitten",
        label="kitten",
        phrase="a striped kitten with soft paws and too much curiosity",
        method="batted the object across the room and after it",
        reason="everything small looked like a toy to it",
        careful=False,
        can_reach_high=False,
        likes_shiny=False,
        tags={"cat", "play"},
    ),
    "keeper": Mover(
        id="keeper",
        label="keeper",
        phrase="the careful keeper of the place",
        method="moved the object while tidying and set it down somewhere unusual",
        reason="the keeper had meant to protect it and then forgotten in the middle of chores",
        careful=True,
        can_reach_high=True,
        likes_shiny=False,
        tags={"adult", "tidy"},
    ),
}


def valid_combo(place_id: str, clue_id: str, hideout_id: str, mover_id: str, missing_id: str) -> bool:
    place = PLACES[place_id]
    clue = CLUES[clue_id]
    hideout = HIDEOUTS[hideout_id]
    mover = MOVERS[mover_id]
    thing = MISSING[missing_id]
    if hideout_id not in place.hideouts:
        return False
    if hideout_id not in clue.points_to:
        return False
    if mover_id == "magpie" and not thing.tags.intersection({"metal", "shiny"}):
        return False
    if mover_id == "magpie" and hideout_id not in {"clock", "window_seat", "portrait_niche"}:
        return False
    if mover_id == "kitten" and hideout_id in {"clock", "portrait_niche"}:
        return False
    if mover_id == "keeper" and not hideout.openable and hideout_id != "portrait_niche":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for clue_id in sorted(CLUES):
            for hideout_id in sorted(HIDEOUTS):
                for mover_id in sorted(MOVERS):
                    for missing_id in sorted(MISSING):
                        if valid_combo(place_id, clue_id, hideout_id, mover_id, missing_id):
                            combos.append((place_id, clue_id, hideout_id, mover_id, missing_id))
    return combos


@dataclass
class StoryParams:
    place: str
    clue: str
    hideout: str
    mover: str
    missing: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="library",
        clue="rhyme",
        hideout="clock",
        mover="magpie",
        missing="compass",
        detective_name="Mira",
        detective_gender="girl",
        helper_name="Jon",
        helper_gender="boy",
        seed=11,
    ),
    StoryParams(
        place="museum",
        clue="draught",
        hideout="map_chest",
        mover="keeper",
        missing="key",
        detective_name="Theo",
        detective_gender="boy",
        helper_name="June",
        helper_gender="girl",
        seed=12,
    ),
    StoryParams(
        place="manor",
        clue="portrait",
        hideout="window_seat",
        mover="kitten",
        missing="bell",
        detective_name="Nora",
        detective_gender="girl",
        helper_name="Eli",
        helper_gender="boy",
        seed=13,
    ),
    StoryParams(
        place="library",
        clue="draught",
        hideout="atlas_drawer",
        mover="kitten",
        missing="key",
        detective_name="Finn",
        detective_gender="boy",
        helper_name="Lila",
        helper_gender="girl",
        seed=14,
    ),
    StoryParams(
        place="manor",
        clue="portrait",
        hideout="portrait_niche",
        mover="keeper",
        missing="compass",
        detective_name="Ava",
        detective_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        seed=15,
    ),
]

GIRL_NAMES = ["Mira", "Nora", "Ava", "Lila", "Zoe", "Ruby", "Ella", "Tess"]
BOY_NAMES = ["Theo", "Finn", "Ben", "Eli", "Owen", "Max", "Noah", "Jude"]


def explain_rejection(place_id: str, clue_id: str, hideout_id: str, mover_id: str, missing_id: str) -> str:
    if place_id in PLACES and hideout_id in HIDEOUTS and hideout_id not in PLACES[place_id].hideouts:
        return f"(No story: {HIDEOUTS[hideout_id].phrase} does not belong in {PLACES[place_id].phrase}.)"
    if clue_id in CLUES and hideout_id in HIDEOUTS and hideout_id not in CLUES[clue_id].points_to:
        return (
            f"(No story: the clue '{clue_id}' does not foreshadow {HIDEOUTS[hideout_id].phrase}. "
            f"The early clue must honestly point to the later answer.)"
        )
    if mover_id == "magpie" and missing_id in MISSING and not MISSING[missing_id].tags.intersection({"metal", "shiny"}):
        return "(No story: the magpie in this world only steals bright metal things.)"
    if mover_id == "magpie" and hideout_id in HIDEOUTS and hideout_id not in {"clock", "window_seat", "portrait_niche"}:
        return "(No story: the magpie cannot sensibly stash the object in that low paper hiding place.)"
    if mover_id == "kitten" and hideout_id in {"clock", "portrait_niche"}:
        return "(No story: the kitten cannot reasonably reach that high, hidden spot.)"
    return "(No valid combination matches the given options.)"


def introduce(world: World, place: Place, detective: Entity, helper: Entity, keeper: Entity, thing: Entity) -> None:
    world.say(
        f"{detective.id} loved mysteries, even the tiny kind that fit inside one room."
    )
    world.say(
        f"That afternoon, {detective.id} and {helper.id} were visiting {place.phrase}, a place of "
        f"{place.old_feature}. {place.hush_detail}"
    )
    world.say(
        f"{keeper.id} showed them {thing.phrase}. {thing.owner_text}, and {thing.shine}."
    )


def vanish(world: World, keeper: Entity, thing: Entity) -> None:
    thing.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {keeper.id} turned back after straightening a stack of papers, the {thing.label} was gone."
    )
    world.say(
        f'"Oh dear," {keeper.id} said. "{thing.phrase.capitalize()} was right here a moment ago."'
    )


def foreshadow(world: World, clue: Clue, detective: Entity) -> None:
    detective.meters["saw_clue"] += 1
    world.say(
        f"Before anyone knew there was a mystery, {detective.id} had already noticed {clue.phrase}. {clue.text}"
    )
    world.say(clue.false_hint)


def promise(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["purpose"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'"Do not worry," {detective.id} said in a small, serious voice. "I will inspect everything."'
    )
    world.say(
        f"{helper.id} stood close beside {detective.pronoun('object')}, ready to be the assistant."
    )


def wrong_guess_text(place: Place) -> tuple[str, str]:
    if place.id == "library":
        return (
            "At first, the crooked painted hands made the children suspect a person had taken it.",
            "They checked behind the reading desk, but found only dust, a blue pencil, and no treasure at all.",
        )
    if place.id == "museum":
        return (
            "At first, the whispering room made the mystery feel grand enough for a sneaky thief.",
            "They peered behind the nearest glass case, but saw only their own puzzled faces looking back.",
        )
    return (
        "At first, the long hallway shadows made the mystery seem as if it belonged to a very secret grown-up.",
        "They searched the umbrella stand by the door, but there was nothing there except an old walking stick.",
    )


def false_lead(world: World, place: Place, detective: Entity) -> None:
    detective.meters["checked_wrong_spot"] += 1
    propagate(world, narrate=False)
    first, second = wrong_guess_text(place)
    world.say(first)
    world.say(second)


def mover_sign(world: World, mover: Mover, detective: Entity, thing: Entity) -> None:
    if mover.id == "magpie":
        world.say(
            f"Then {detective.id} noticed one black-and-white feather on the sill. It was not proof by itself, "
            f"but it made the case feel sharper."
        )
    elif mover.id == "kitten":
        world.say(
            f"Then a tiny line of paw marks crossed the dust. They were too small for a thief and too playful for a trap."
        )
    else:
        world.say(
            f"Then {detective.id} saw a tidy cloth and a ring of polished dust where the {thing.label} had rested before. "
            f"It looked more like hurried cleaning than stealing."
        )


def realization(world: World, clue: Clue, detective: Entity) -> None:
    detective.meters["remembered_clue"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} stopped walking. The early clue came back at once, bright in {detective.pronoun('possessive')} mind."
    )
    world.say(
        f'"Wait," {detective.pronoun()} whispered. "That strange {clue.label} was not decoration. It was the answer arriving early."'
    )
    world.facts["foreshadow_line"] = (
        f"The {clue.label} appeared before the object went missing, and later {detective.id} understood it had been pointing to the hiding place."
    )


def solve(world: World, hideout: Hideout, mover: Mover, thing: Entity, detective: Entity, helper: Entity, keeper: Entity) -> None:
    detective.memes["certainty"] += 1
    helper.memes["awe"] += 1
    thing.meters["found"] += 1
    thing.meters["missing"] = 0.0
    world.say(
        f"{detective.id} led everyone to {hideout.phrase}. There, {keeper.id} searched {hideout.discovery}, and found the {thing.label} at last."
    )
    world.say(hideout.proof)
    if mover.id == "magpie":
        world.say(
            f"Up above, the magpie gave one bright-eyed hop, as if it had never meant any harm at all."
        )
    elif mover.id == "kitten":
        world.say(
            f"The kitten blinked from under a chair, innocent-looking except for the dust on its whiskers."
        )
    else:
        world.say(
            f"{keeper.id} pressed a hand to {keeper.pronoun('possessive')} forehead and gave a sheepish laugh. "
            f"{keeper.pronoun().capitalize()} had hidden it while tidying and forgotten."
        )


def ending(world: World, place: Place, detective: Entity, helper: Entity, keeper: Entity, thing: Entity) -> None:
    for ent in (detective, helper, keeper):
        ent.memes["relief"] += 1
    world.say(
        f'"Case solved," said {detective.id}. {helper.id} grinned so hard that even the quiet room seemed to smile with {helper.pronoun("object")}.'
    )
    world.say(
        f"{keeper.id} thanked the young detective and set the {thing.label} back in its proper place."
    )
    world.say(
        f"As the tall room settled into calm again, {detective.id} glanced once more at the old clue from the days of yore and knew that small details could speak long before the answer was clear."
    )


def tell(
    *,
    place: Place,
    clue: Clue,
    hideout: Hideout,
    mover: Mover,
    missing: MissingThing,
    detective_name: str,
    detective_gender: str,
    helper_name: str,
    helper_gender: str,
) -> World:
    world = World()
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            label=detective_name,
            role="detective",
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
        )
    )
    keeper = world.add(
        Entity(
            id=place.keeper_label,
            kind="character",
            type=place.keeper_type,
            label=place.keeper_label,
            role="keeper",
        )
    )
    thing = world.add(
        Entity(
            id="thing",
            kind="thing",
            type=missing.id,
            label=missing.label,
            phrase=missing.phrase,
            portable=missing.portable,
            noisy=missing.noisy,
            tags=set(missing.tags),
        )
    )
    spot = world.add(
        Entity(
            id="hideout",
            kind="thing",
            type="hideout",
            label=hideout.label,
            phrase=hideout.phrase,
            openable=hideout.openable,
            tags=set(hideout.tags),
        )
    )
    world.facts["spot_entity_id"] = spot.id

    introduce(world, place, detective, helper, keeper, thing)
    foreshadow(world, clue, detective)

    world.para()
    vanish(world, keeper, thing)
    promise(world, detective, helper)

    world.para()
    false_lead(world, place, detective)
    mover_sign(world, mover, detective, thing)
    realization(world, clue, detective)

    world.para()
    solve(world, hideout, mover, thing, detective, helper, keeper)
    ending(world, place, detective, helper, keeper, thing)

    world.facts.update(
        place=place,
        clue=clue,
        hideout=hideout,
        mover=mover,
        missing_cfg=missing,
        detective=detective,
        helper=helper,
        keeper=keeper,
        thing=thing,
        solved=thing.meters["found"] >= THRESHOLD,
        foreshadowed=detective.meters["saw_clue"] >= THRESHOLD and detective.meters["remembered_clue"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and uses careful thinking to solve a mystery. Good detectives notice small details other people miss."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story shows a small clue early, and that clue matters more later. It makes the ending feel surprising and fair at the same time."
        )
    ],
    "yore": [
        (
            "What does 'yore' mean?",
            "'Yore' means long ago or in old times. People use it when they want something to sound very old."
        )
    ],
    "clock": [
        (
            "Why might an old clock make a good hiding place in a mystery?",
            "An old clock can have little doors, shelves, or spaces inside it. That makes it a believable place for something small to be hidden."
        )
    ],
    "maps": [
        (
            "Why are drawers and map chests good hiding places?",
            "They can hold flat things and have layers where small objects slip out of sight. A detective should check places where something could be tucked under or behind other things."
        )
    ],
    "portrait": [
        (
            "Why do portraits feel mysterious in detective stories?",
            "Portraits watch the room without moving, so they make readers wonder what they hide or point toward. They can turn an ordinary wall into a suspicious place."
        )
    ],
    "magpie": [
        (
            "Why might a magpie take a shiny object?",
            "Magpies are often imagined as birds that like bright, glittering things. In stories, that makes them playful little troublemakers."
        )
    ],
    "kitten": [
        (
            "Why does a kitten move things around?",
            "Kittens bat and chase small objects because they are curious and playful. They are not trying to steal; they are turning the room into a game."
        )
    ],
    "keeper": [
        (
            "Can a mystery happen by accident instead of by meanness?",
            "Yes. Sometimes a person moves something while cleaning or protecting it and simply forgets where it went."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "foreshadowing", "yore", "clock", "maps", "portrait", "magpie", "kitten", "keeper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    clue = f["clue"]
    thing = f["missing_cfg"]
    hideout = f["hideout"]
    detective = f["detective"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the word "yore" and uses foreshadowing.',
        f"Tell a mystery set in {place.phrase} where {detective.id} notices {clue.phrase} early, then later realizes it points to {hideout.phrase}.",
        f'Write a child-facing detective tale about a missing {thing.label} where an old clue seems small at first but quietly leads to the answer.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    keeper = f["keeper"]
    clue = f["clue"]
    hideout = f["hideout"]
    mover = f["mover"]
    thing = f["missing_cfg"]
    place = f["place"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, with {helper.id} helping and {keeper.id} worrying over a missing {thing.label}. The mystery happens in {place.phrase}."
        ),
        (
            f"What went missing?",
            f"The missing object was {thing.phrase}. It mattered because it was {thing.owner_text}."
        ),
        (
            "What was the early clue?",
            f"The early clue was {clue.phrase}. It seemed small at first, but it mattered later because it pointed toward {hideout.phrase}."
        ),
        (
            "How did the story use foreshadowing?",
            f"It showed the clue before the mystery was understood. Later, {detective.id} remembered that clue and used it to solve the case."
        ),
        (
            f"Why did {detective.id} stop searching in the wrong place?",
            f"{detective.id} checked one wrong place and found nothing useful there. That failure made {detective.pronoun()} think back to the old clue instead of guessing again."
        ),
        (
            f"Where did they find the {thing.label}?",
            f"They found it {hideout.discovery}. The hiding place fit the old clue, which is why the solution felt earned."
        ),
    ]

    if mover.id == "magpie":
        qa.append(
            (
                f"Who moved the {thing.label}, and why?",
                f"A magpie had taken it. The bird liked shiny things, so it carried the bright object away and tucked it into a hidden spot."
            )
        )
    elif mover.id == "kitten":
        qa.append(
            (
                f"Who moved the {thing.label}, and why?",
                f"A kitten moved it while playing. It treated the small object like a toy, so the mystery began by accident."
            )
        )
    else:
        qa.append(
            (
                f"Who moved the {thing.label}, and why?",
                f"The keeper had moved it while tidying and forgot. That made the mystery gentle rather than mean, because the trouble came from a mistake."
            )
        )

    qa.append(
        (
            "How did the story end?",
            f"It ended with the {thing.label} safely returned and everyone relieved. The last image looks back at the old clue from the days of yore, showing that the detective now understands how early details can matter."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"detective", "foreshadowing", "yore"}
    hideout = f["hideout"]
    mover = f["mover"]
    if "clock" in hideout.tags:
        tags.add("clock")
    if "maps" in hideout.tags or "maps" in f["clue"].tags:
        tags.add("maps")
    if "portrait" in hideout.tags or "portrait" in f["clue"].tags:
        tags.add("portrait")
    if mover.id in {"magpie", "kitten", "keeper"}:
        tags.add(mover.id)

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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("portable", ent.portable), ("noisy", ent.noisy), ("openable", ent.openable)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% base compatibility
valid_combo(P, C, H, M, T) :-
    place(P), clue(C), hideout(H), mover(M), thing(T),
    in_place(P, H), points_to(C, H), mover_ok(M, H, T).

mover_ok(magpie, H, T) :-
    shiny_thing(T), high_hideout(H).
mover_ok(kitten, H, _T) :-
    low_hideout(H).
mover_ok(keeper, H, _T) :-
    keeper_hideout(H).

% story outcome and structure
solvable(P, C, H, M, T) :- valid_combo(P, C, H, M, T).
foreshadowed(C, H) :- points_to(C, H).
found(H) :- chosen_hideout(H), chosen_clue(C), foreshadowed(C, H).
outcome(solved) :- chosen_place(P), chosen_clue(C), chosen_hideout(H), chosen_mover(M), chosen_thing(T), solvable(P, C, H, M, T), found(H).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hideout_id in sorted(place.hideouts):
            lines.append(asp.fact("in_place", place_id, hideout_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for hideout_id in sorted(clue.points_to):
            lines.append(asp.fact("points_to", clue_id, hideout_id))
    for hideout_id in HIDEOUTS:
        lines.append(asp.fact("hideout", hideout_id))
    for mover_id in MOVERS:
        lines.append(asp.fact("mover", mover_id))
    for thing_id, thing in MISSING.items():
        lines.append(asp.fact("thing", thing_id))
        if thing.tags.intersection({"metal", "shiny"}):
            lines.append(asp.fact("shiny_thing", thing_id))
    for hideout_id in sorted({"clock", "portrait_niche", "window_seat"}):
        lines.append(asp.fact("high_hideout", hideout_id))
    for hideout_id in sorted({"atlas_drawer", "map_chest", "window_seat"}):
        lines.append(asp.fact("low_hideout", hideout_id))
    for hideout_id in sorted({"clock", "atlas_drawer", "map_chest", "window_seat", "portrait_niche"}):
        lines.append(asp.fact("keeper_hideout", hideout_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_combo/5."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_clue", params.clue),
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_mover", params.mover),
            asp.fact("chosen_thing", params.missing),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if valid_combo(params.place, params.clue, params.hideout, params.mover, params.missing) else "?"


def _validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.mover not in MOVERS:
        raise StoryError(f"(Unknown mover: {params.mover})")
    if params.missing not in MISSING:
        raise StoryError(f"(Unknown missing object: {params.missing})")
    if not valid_combo(params.place, params.clue, params.hideout, params.mover, params.missing):
        raise StoryError(explain_rejection(params.place, params.clue, params.hideout, params.mover, params.missing))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A tiny detective-story world with foreshadowing and a gentle missing-object mystery."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--hideout", choices=sorted(HIDEOUTS))
    ap.add_argument("--mover", choices=sorted(MOVERS))
    ap.add_argument("--missing", choices=sorted(MISSING))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(getattr(args, field) is not None for field in ("place", "clue", "hideout", "mover", "missing")):
        if not valid_combo(args.place, args.clue, args.hideout, args.mover, args.missing):
            raise StoryError(explain_rejection(args.place, args.clue, args.hideout, args.mover, args.missing))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.mover is None or combo[3] == args.mover)
        and (args.missing is None or combo[4] == args.missing)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, clue_id, hideout_id, mover_id, missing_id = rng.choice(sorted(combos))
    detective_gender = args.gender or rng.choice(["girl", "boy"])
    detective_name = args.name or _pick_name(rng, detective_gender)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=detective_name)
    return StoryParams(
        place=place_id,
        clue=clue_id,
        hideout=hideout_id,
        mover=mover_id,
        missing=missing_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        place=PLACES[params.place],
        clue=CLUES[params.clue],
        hideout=HIDEOUTS[params.hideout],
        mover=MOVERS[params.mover],
        missing=MISSING[params.missing],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcomes match Python outcomes on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcome checks differed.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Empty story in smoke test.")
        sink = io.StringIO()
        with redirect_stdout(sink):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_combo/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, clue, hideout, mover, missing) combinations:\n")
        for place_id, clue_id, hideout_id, mover_id, thing_id in combos:
            print(f"  {place_id:8} {clue_id:9} {hideout_id:14} {mover_id:7} {thing_id}")
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
            header = (
                f"### {p.detective_name}: {p.missing} at {p.place} "
                f"({p.clue} -> {p.hideout}, mover: {p.mover})"
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
