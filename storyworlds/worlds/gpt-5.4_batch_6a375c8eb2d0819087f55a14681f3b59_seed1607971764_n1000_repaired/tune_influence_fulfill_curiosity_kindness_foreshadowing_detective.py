#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tune_influence_fulfill_curiosity_kindness_foreshadowing_detective.py
================================================================================================

A standalone storyworld for a gentle child-sized detective story: something useful
has gone missing, a faint tune foreshadows where the clue trail leads, and a kind
young detective solves the mystery without blaming anyone.

The domain is built around three ideas:
- Curiosity: the detective notices a small odd detail and keeps following it.
- Kindness: a gentle approach can influence whether a shy borrower speaks up.
- Foreshadowing: an early tune quietly points toward the hiding place before the
  truth is understood.

The stories are not template swaps. A live world state tracks missing objects,
worry, curiosity, trust, clues, confession, recovery, and fulfilled kindness.
That state drives both the prose and the Q&A.

Run it
------
    python storyworlds/worlds/gpt-5.4/tune_influence_fulfill_curiosity_kindness_foreshadowing_detective.py
    python storyworlds/worlds/gpt-5.4/tune_influence_fulfill_curiosity_kindness_foreshadowing_detective.py --place library --item umbrella --mission rain_walk
    python storyworlds/worlds/gpt-5.4/tune_influence_fulfill_curiosity_kindness_foreshadowing_detective.py --approach stern
    python storyworlds/worlds/gpt-5.4/tune_influence_fulfill_curiosity_kindness_foreshadowing_detective.py --all
    python storyworlds/worlds/gpt-5.4/tune_influence_fulfill_curiosity_kindness_foreshadowing_detective.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tune_influence_fulfill_curiosity_kindness_foreshadowing_detective.py --verify
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
KINDNESS_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man", "groundskeeper"}
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
            "librarian": "librarian",
            "groundskeeper": "groundskeeper",
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
class Place:
    id: str
    label: str
    opening: str
    keeper_type: str
    keeper_label: str
    hiding_spot: str
    clue_sound: str
    clue_source: str
    clue_line: str
    supports: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    the: str
    use: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Mission:
    id: str
    need_item: str
    beneficiary: str
    promise: str
    action: str
    result: str
    closing_image: str
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
class Approach:
    id: str
    kindness: int
    ask: str
    reassurance: str
    qa_phrase: str
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


def _r_missing_worry(world: World) -> list[str]:
    keeper = world.get("keeper")
    detective = world.get("detective")
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keeper.memes["worry"] += 1
    detective.memes["curiosity"] += 1
    return ["__missing__"]


def _r_clue_pull(world: World) -> list[str]:
    detective = world.get("detective")
    if detective.memes["curiosity"] < THRESHOLD or world.facts["clue_heard"] < THRESHOLD:
        return []
    sig = ("clue_pull", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.meters["investigating"] += 1
    return ["__clue__"]


def _r_kindness_trust(world: World) -> list[str]:
    borrower = world.get("borrower")
    approach = world.facts["approach_cfg"]
    if world.facts["asked_kindly"] < THRESHOLD:
        return []
    sig = ("kindness_trust", borrower.id, approach.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    borrower.memes["trust"] += float(approach.kindness)
    return ["__trust__"]


def _r_confess(world: World) -> list[str]:
    borrower = world.get("borrower")
    if borrower.memes["trust"] < 3.0:
        return []
    if world.facts["item_found"] >= THRESHOLD:
        return []
    sig = ("confess", borrower.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["confessed"] = 1.0
    borrower.memes["relief"] += 1
    return ["__confess__"]


def _r_recovery(world: World) -> list[str]:
    item = world.get("item")
    keeper = world.get("keeper")
    detective = world.get("detective")
    if world.facts["confessed"] < THRESHOLD and world.facts["item_found"] < THRESHOLD:
        return []
    sig = ("recovery", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["recovered"] += 1
    keeper.memes["worry"] = 0.0
    keeper.memes["relief"] += 1
    detective.memes["pride"] += 1
    return ["__recovery__"]


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="clue_pull", tag="physical", apply=_r_clue_pull),
    Rule(name="kindness_trust", tag="social", apply=_r_kindness_trust),
    Rule(name="confess", tag="social", apply=_r_confess),
    Rule(name="recovery", tag="social", apply=_r_recovery),
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
        for s in produced:
            world.say(s)
    return produced


def item_matches_mission(item: MissingItem, mission: Mission) -> bool:
    return item.id == mission.need_item


def sensible_approaches() -> list[Approach]:
    return [a for a in APPROACHES.values() if a.kindness >= KINDNESS_MIN]


def outcome_of(params: "StoryParams") -> str:
    approach = APPROACHES[params.approach]
    return "confessed" if approach.kindness >= 3 else "discovered"


def predict_confession(world: World, approach: Approach) -> bool:
    sim = world.copy()
    sim.facts["approach_cfg"] = approach
    sim.facts["asked_kindly"] = 1.0
    propagate(sim, narrate=False)
    return sim.facts["confessed"] >= THRESHOLD


def introduce(world: World, detective: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"{detective.id} liked mysteries, even tiny ones, and {friend.id} liked tagging along. "
        f"That afternoon they were at {place.label}, where {place.opening}"
    )
    world.say(
        f"As they walked in, {detective.id} paused. Somewhere near {place.hiding_spot}, "
        f"{place.clue_line}"
    )
    world.facts["clue_heard"] = 1.0


def discover_missing(world: World, keeper: Entity, item: Entity, cfg: MissingItem) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {keeper.label_word} looked around and blinked. "
        f'"Oh dear," {keeper.pronoun()} said. "{cfg.The} is gone."'
    )
    world.say(
        f"{detective.id}'s eyes sharpened at once. A missing {cfg.label} was exactly the sort of case "
        f"{detective.pronoun()} loved to solve."
    )


def describe_need(world: World, keeper: Entity, mission: Mission, item: MissingItem) -> None:
    world.say(
        f'"We needed {item.the} to {item.use}," {keeper.label_word} explained. '
        f'"Without it, we cannot {mission.result}."'
    )


def inspect_clue(world: World, detective: Entity, friend: Entity, place: Place) -> None:
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} tipped {detective.pronoun("possessive")} head. '
        f'"That {place.clue_sound} again," {detective.pronoun()} whispered.'
    )
    world.say(
        f"{friend.id} glanced toward {place.hiding_spot}. "
        f'"Maybe the tune means something," {friend.pronoun()} said.'
    )


def search_spot(world: World, detective: Entity, place: Place) -> None:
    world.say(
        f"Step by step, {detective.id} followed the sound to {place.hiding_spot}. "
        f"There, tucked beside {place.clue_source}, lay one fresh clue: a little scrap of ribbon."
    )
    world.facts["trail_seen"] = 1.0


def ask_kindly(world: World, detective: Entity, borrower: Entity, approach: Approach, mission: Mission) -> None:
    world.facts["asked_kindly"] = 1.0
    world.facts["approach_cfg"] = approach
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} found {borrower.id} nearby and did not point or accuse. '
        f'{approach.ask}'
    )
    if predict_confession(world, approach):
        world.say(
            f'{borrower.id} looked down at the ribbon in {borrower.pronoun("possessive")} fingers. '
            f'{approach.reassurance}'
        )
    else:
        world.say(
            f"{borrower.id} fidgeted and stayed quiet, but {detective.id} noticed the ribbon matched the clue "
            f"by {place_name(world)}."
        )


def place_name(world: World) -> str:
    return world.place.hiding_spot


def confess(world: World, borrower: Entity, item_cfg: MissingItem, mission: Mission) -> None:
    propagate(world, narrate=False)
    world.say(
        f'"I borrowed {item_cfg.the}," {borrower.id} admitted at last. '
        f'"I was trying to fulfill a promise to {mission.beneficiary} and got scared when I thought I had made a mess of it."'
    )


def deduce(world: World, detective: Entity, borrower: Entity, item_cfg: MissingItem, mission: Mission) -> None:
    world.say(
        f'{detective.id} spoke softly. "The ribbon, the {world.place.clue_source}, and that tune all lead to the same place," '
        f'{detective.pronoun()} said. "You borrowed {item_cfg.the} for something kind."'
    )
    world.facts["item_found"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{borrower.id}'s shoulders dropped with relief. "
        f'"Yes," {borrower.pronoun()} whispered. "I wanted to fulfill my promise to {mission.beneficiary}."'
    )


def recover_item(world: World, detective: Entity, borrower: Entity, keeper: Entity, item_cfg: MissingItem, mission: Mission) -> None:
    if world.facts["confessed"] >= THRESHOLD:
        world.say(
            f"Together they lifted {item_cfg.the} out from behind {world.place.clue_source}. "
            f"It had been hidden there all along while {borrower.id} hurried to finish the surprise."
        )
    else:
        world.say(
            f"Behind {world.place.clue_source}, {detective.id} found {item_cfg.the}. "
            f"{borrower.id} nodded, too embarrassed to pretend anymore."
        )
    world.facts["item_found"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{keeper.label_word.capitalize()} let out a long breath. "
        f'"So that was the mystery," {keeper.pronoun()} said.'
    )
    world.say(
        f"No one scolded. Kindness had more influence than blame, and that made the truth easier to tell."
    )


def fulfill_kind_plan(world: World, detective: Entity, friend: Entity, borrower: Entity, mission: Mission) -> None:
    detective.memes["kindness"] += 1
    borrower.memes["gratitude"] += 1
    world.say(
        f"Instead of ending the plan, they all helped finish it. "
        f"With the case solved, they used the missing thing to {mission.action}."
    )
    world.say(
        f"Soon {mission.result}. {mission.closing_image}"
    )


def tell(
    place: Place,
    item_cfg: MissingItem,
    mission: Mission,
    approach: Approach,
    detective_name: str = "Nora",
    detective_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    borrower_name: str = "Milo",
    borrower_gender: str = "boy",
) -> World:
    world = World(place)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        label=detective_name,
        role="detective",
        traits=["curious", "kind"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["steady"],
    ))
    borrower = world.add(Entity(
        id=borrower_name,
        kind="character",
        type=borrower_gender,
        label=borrower_name,
        role="borrower",
        traits=["shy"],
    ))
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type=place.keeper_type,
        label=place.keeper_label,
        role="keeper",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        role="missing_item",
        owner="keeper",
    ))

    world.facts.update(
        clue_heard=0.0,
        trail_seen=0.0,
        asked_kindly=0.0,
        confessed=0.0,
        item_found=0.0,
        place_cfg=place,
        item_cfg=item_cfg,
        mission_cfg=mission,
        approach_cfg=approach,
        detective=detective,
        friend=friend,
        borrower=borrower,
        keeper=keeper,
        item=item,
    )

    introduce(world, detective, friend, place)
    discover_missing(world, keeper, item, item_cfg)
    describe_need(world, keeper, mission, item_cfg)

    world.para()
    inspect_clue(world, detective, friend, place)
    search_spot(world, detective, place)
    ask_kindly(world, detective, borrower, approach, mission)

    world.para()
    if world.facts["confessed"] >= THRESHOLD:
        confess(world, borrower, item_cfg, mission)
    else:
        deduce(world, detective, borrower, item_cfg, mission)
    recover_item(world, detective, borrower, keeper, item_cfg, mission)

    world.para()
    fulfill_kind_plan(world, detective, friend, borrower, mission)

    world.facts["outcome"] = "confessed" if world.facts["confessed"] >= THRESHOLD else "discovered"
    return world


PLACES = {
    "library": Place(
        id="library",
        label="the little library",
        opening="dusty sunbeams fell across the floor and the returned books made neat towers by the desk.",
        keeper_type="librarian",
        keeper_label="the librarian",
        hiding_spot="the coat nook",
        clue_sound="music-box tune",
        clue_source="a tin lunchbox painted with moons",
        clue_line="a tiny music-box tune chimed once and then went still.",
        supports={"book_delivery", "rain_walk"},
        tags={"library", "music"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the brick courtyard",
        opening="flower pots lined the wall and a bench sat under the sycamore tree.",
        keeper_type="mother",
        keeper_label="the caretaker",
        hiding_spot="the bench with the loose slat",
        clue_sound="whistled tune",
        clue_source="a skipping rope curled like a red question mark",
        clue_line="someone was whistling a crooked tune and then trying to swallow it.",
        supports={"muffins", "rain_walk"},
        tags={"courtyard", "music"},
    ),
    "garden": Place(
        id="garden",
        label="the community garden",
        opening="watering cans glittered by the gate and rows of leaves trembled in the breeze.",
        keeper_type="groundskeeper",
        keeper_label="the groundskeeper",
        hiding_spot="the potting bench",
        clue_sound="hummed tune",
        clue_source="a seed packet box tied with green string",
        clue_line="a low hummed tune drifted from the potting bench and seemed to hide when they looked that way.",
        supports={"seedlings", "muffins"},
        tags={"garden", "music"},
    ),
}

ITEMS = {
    "wagon": MissingItem(
        id="wagon",
        label="wagon",
        phrase="a little red wagon",
        the="the little red wagon",
        use="move heavy things without dropping them",
        tags={"wagon", "helping"},
    ),
    "basket": MissingItem(
        id="basket",
        label="basket",
        phrase="a round willow basket",
        the="the willow basket",
        use="carry treats carefully",
        tags={"basket", "helping"},
    ),
    "umbrella": MissingItem(
        id="umbrella",
        label="umbrella",
        phrase="a big yellow umbrella",
        the="the yellow umbrella",
        use="keep someone dry on a wet walk",
        tags={"umbrella", "rain"},
    ),
}

MISSIONS = {
    "book_delivery": Mission(
        id="book_delivery",
        need_item="wagon",
        beneficiary="Mr. Hale, whose leg was sore",
        promise="bring a stack of library books to the front step",
        action="roll a stack of library books to Mr. Hale's front step",
        result="Mr. Hale got his books without carrying anything heavy",
        closing_image="The wagon creaked home empty, and the mystery felt warm instead of scary.",
        tags={"books", "kindness"},
    ),
    "seedlings": Mission(
        id="seedlings",
        need_item="wagon",
        beneficiary="Mrs. Vale, who could not lift the seed trays alone",
        promise="bring the seedling trays to the sunny patch",
        action="pull the seedling trays to the sunny patch",
        result="the seedlings reached the sun before their leaves drooped",
        closing_image="The tiny plants stood straighter in the light, as if they knew the case had been solved for them too.",
        tags={"garden", "kindness"},
    ),
    "muffins": Mission(
        id="muffins",
        need_item="basket",
        beneficiary="the crossing guard at the corner",
        promise="carry warm muffins without squashing them",
        action="carry warm muffins to the corner",
        result="the crossing guard received the muffins still warm and whole",
        closing_image="A sweet smell floated behind them, and even the detective shoes seemed to walk lighter.",
        tags={"food", "kindness"},
    ),
    "rain_walk": Mission(
        id="rain_walk",
        need_item="umbrella",
        beneficiary="Mrs. Inez, who had forgotten her own umbrella",
        promise="walk Mrs. Inez home before the drizzle turned into rain",
        action="walk beside Mrs. Inez under the umbrella",
        result="Mrs. Inez reached home dry, smiling under the bright yellow circle",
        closing_image="Raindrops ticked on the cloth like tiny applause, and the mystery ended in a dry doorway.",
        tags={"rain", "kindness"},
    ),
}

APPROACHES = {
    "gentle": Approach(
        id="gentle",
        kindness=3,
        ask='"If you know something, you can tell us," '
            'said the young detective. "We are here to help, not to make anyone feel small."',
        reassurance='"I only wanted to help too," said the detective.',
        qa_phrase="spoke so gently that the shy borrower confessed",
        tags={"kindness"},
    ),
    "patient": Approach(
        id="patient",
        kindness=2,
        ask='"We can look together," '
            'said the young detective. "No one is in trouble for trying to do a kind thing."',
        reassurance='"Take your time," said the detective.',
        qa_phrase="asked kindly, then used the clues to discover the truth",
        tags={"kindness"},
    ),
    "stern": Approach(
        id="stern",
        kindness=1,
        ask='"Someone had better explain this right now," '
            'said the detective, too sharply for a frightened helper.',
        reassurance='"Just say it," said the detective.',
        qa_phrase="pressed too hard and made the truth hide deeper",
        tags={"blame"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Ruby", "Clara"]
BOY_NAMES = ["Ben", "Max", "Leo", "Theo", "Finn", "Milo", "Eli", "Sam"]


@dataclass
class StoryParams:
    place: str
    item: str
    mission: str
    approach: str
    detective_name: str
    detective_gender: str
    friend_name: str
    friend_gender: str
    borrower_name: str
    borrower_gender: str
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


CURATED = [
    StoryParams(
        place="library",
        item="wagon",
        mission="book_delivery",
        approach="gentle",
        detective_name="Nora",
        detective_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        borrower_name="Milo",
        borrower_gender="boy",
        seed=1,
    ),
    StoryParams(
        place="garden",
        item="wagon",
        mission="seedlings",
        approach="patient",
        detective_name="Theo",
        detective_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        borrower_name="Ava",
        borrower_gender="girl",
        seed=2,
    ),
    StoryParams(
        place="courtyard",
        item="basket",
        mission="muffins",
        approach="gentle",
        detective_name="Clara",
        detective_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        borrower_name="Eli",
        borrower_gender="boy",
        seed=3,
    ),
    StoryParams(
        place="library",
        item="umbrella",
        mission="rain_walk",
        approach="patient",
        detective_name="Finn",
        detective_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        borrower_name="Lily",
        borrower_gender="girl",
        seed=4,
    ),
]


KNOWLEDGE = {
    "music": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is a small early clue that hints at something important later. A tune, a footprint, or a missing ribbon can prepare the reader before the mystery is solved."
        )
    ],
    "kindness": [
        (
            "Why can kindness help in a mystery?",
            "Kindness can make frightened people feel safe enough to tell the truth. When someone stops feeling blamed, it is often easier for them to explain what really happened."
        )
    ],
    "wagon": [
        (
            "What is a wagon used for?",
            "A wagon helps carry heavy things from one place to another. It makes a kind job easier when arms alone would tire quickly."
        )
    ],
    "basket": [
        (
            "What is a basket good for?",
            "A basket holds things gently while you carry them. That is useful for soft treats or small supplies that might get squashed."
        )
    ],
    "umbrella": [
        (
            "What does an umbrella do?",
            "An umbrella spreads over your head and shoulders to keep rain off. It helps people walk outside without getting soaked."
        )
    ],
    "books": [
        (
            "Why might someone bring books to a neighbor?",
            "Bringing books can cheer up someone who cannot get out easily. It is a simple kind act because stories and company can travel even when people cannot."
        )
    ],
    "garden": [
        (
            "Why do seedlings need sun and careful handling?",
            "Seedlings are young plants, so they can droop or break more easily than big plants. Gentle hands and enough sunlight help them keep growing."
        )
    ],
    "food": [
        (
            "Why does carrying warm food carefully matter?",
            "Careful carrying keeps the food from getting smashed or spilled. It also helps the person receiving it enjoy the treat the way it was meant to be shared."
        )
    ],
    "rain": [
        (
            "Why is it kind to share an umbrella?",
            "Sharing an umbrella keeps another person dry and comfortable. It is a small way to notice what someone needs and help right away."
        )
    ],
}
KNOWLEDGE_ORDER = ["music", "kindness", "wagon", "basket", "umbrella", "books", "garden", "food", "rain"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mission_id in sorted(place.supports):
            mission = MISSIONS[mission_id]
            item = ITEMS[mission.need_item]
            if item_matches_mission(item, mission):
                combos.append((place_id, item.id, mission_id))
    return combos


def explain_combo_rejection(place: Optional[str], item: MissingItem, mission: Mission) -> str:
    allowed_places = sorted(pid for pid, pl in PLACES.items() if mission.id in pl.supports)
    if not item_matches_mission(item, mission):
        return (
            f"(No story: {item.the} does not fit this kind plan. "
            f'To {mission.action}, the story needs {ITEMS[mission.need_item].the} instead.)'
        )
    if place and mission.id not in PLACES[place].supports:
        return (
            f"(No story: {PLACES[place].label} does not fit the mission '{mission.id}'. "
            f"Try one of these places: {', '.join(allowed_places)}.)"
        )
    return "(No story: this place, item, and mission do not form a grounded mystery.)"


def explain_approach_rejection(approach_id: str) -> str:
    a = APPROACHES[approach_id]
    better = ", ".join(sorted(x.id for x in sensible_approaches()))
    return (
        f"(Refusing approach '{approach_id}': it is too harsh for a kindness-first detective story "
        f"(kindness={a.kindness} < {KINDNESS_MIN}). Try: {better}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    item = f["item_cfg"]
    mission = f["mission_cfg"]
    place = f["place_cfg"]
    outcome = f["outcome"]
    style = "gentle detective story"
    if outcome == "confessed":
        middle = "the detective's kindness influences a shy helper to confess"
    else:
        middle = "the detective kindly follows clues and discovers the truth"
    return [
        f'Write a {style} for a 3-to-5-year-old where a missing {item.label}, a strange tune, and one kind clue lead to a happy ending.',
        f"Tell a mystery set in {place.label} where {det.id} notices a clue before anyone understands it, and {middle}.",
        f'Write a child-facing detective story that uses the words "tune", "influence", and "fulfill", and ends with a kind plan being fulfilled.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    friend = f["friend"]
    borrower = f["borrower"]
    keeper = f["keeper"]
    place = f["place_cfg"]
    item = f["item_cfg"]
    mission = f["mission_cfg"]
    approach = f["approach_cfg"]
    outcome = f["outcome"]

    qa = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a young detective, {friend.id}, who helps with the search, and {borrower.id}, the shy borrower. The mystery begins when {keeper.label_word} notices that {item.the} is missing."
        ),
        (
            f"What was the first clue in the mystery?",
            f"The first clue was {place.clue_sound} near {place.hiding_spot}. That tune was foreshadowing, because it pointed toward the hiding place before the children understood why it mattered."
        ),
        (
            f"Why had {item.the} gone missing?",
            f"It had been borrowed for a kind reason: {borrower.id} wanted to fulfill a promise to {mission.beneficiary}. The missing thing was needed so they could {mission.action}."
        ),
    ]
    if outcome == "confessed":
        qa.append(
            (
                f"How did {detective.id} solve the case?",
                f"{detective.id} {approach.qa_phrase}. That mattered because kindness gave {borrower.id} enough trust to stop hiding and explain the real reason."
            )
        )
    else:
        qa.append(
            (
                f"How did {detective.id} solve the case?",
                f"{detective.id} asked kindly first, then followed the clue from the tune to {place.hiding_spot}. The gentle approach still mattered, because it kept the mystery calm enough for {borrower.id} to admit the kind plan once the item was found."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The case ended happily because everyone used the missing thing to {mission.action}. The last image proves what changed: {mission.closing_image}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place_cfg"].tags) | set(f["item_cfg"].tags) | set(f["mission_cfg"].tags) | {"kindness"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    facts = {
        k: v for k, v in world.facts.items()
        if isinstance(v, (str, int, float, bool))
    }
    lines.append(f"  facts={facts}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- catalog reasoning -----------------------------------------------------
fits_item(M, I) :- mission(M), mission_needs(M, I), item(I).
supported(P, M) :- place(P), place_supports(P, M).
valid(P, I, M)  :- supported(P, M), fits_item(M, I).

% --- kindness gate ---------------------------------------------------------
sensible_approach(A) :- approach(A), kindness(A, K), kindness_min(M), K >= M.

% --- outcome model ---------------------------------------------------------
confessed  :- chosen_approach(A), kindness(A, K), K >= 3.
discovered :- chosen_approach(A), kindness(A, K), K < 3.
outcome(confessed) :- confessed.
outcome(discovered) :- discovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(place.supports):
            lines.append(asp.fact("place_supports", pid, m))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_needs", mid, mission.need_item))
    for aid, app in APPROACHES.items():
        lines.append(asp.fact("approach", aid))
        lines.append(asp.fact("kindness", aid, app.kindness))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_approaches() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_approach/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible_approach"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_approach", params.approach)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle detective storyworld with curiosity, kindness, and foreshadowing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--detective-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--borrower-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--borrower-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render a curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.approach and APPROACHES[args.approach].kindness < KINDNESS_MIN:
        raise StoryError(explain_approach_rejection(args.approach))

    if args.item and args.mission:
        item = ITEMS[args.item]
        mission = MISSIONS[args.mission]
        if not item_matches_mission(item, mission):
            raise StoryError(explain_combo_rejection(args.place, item, mission))
        if args.place and args.mission not in PLACES[args.place].supports:
            raise StoryError(explain_combo_rejection(args.place, item, mission))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.item is None or c[1] == args.item)
        and (args.mission is None or c[2] == args.mission)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, mission = rng.choice(sorted(combos))
    approach = args.approach or rng.choice(sorted(a.id for a in sensible_approaches()))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    borrower_gender = args.borrower_gender or rng.choice(["girl", "boy"])

    used: set[str] = set()
    detective_name = args.detective_name or _pick_name(rng, detective_gender, used)
    used.add(detective_name)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, used)
    used.add(friend_name)
    borrower_name = args.borrower_name or _pick_name(rng, borrower_gender, used)

    return StoryParams(
        place=place,
        item=item,
        mission=mission,
        approach=approach,
        detective_name=detective_name,
        detective_gender=detective_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        borrower_name=borrower_name,
        borrower_gender=borrower_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")

    place = PLACES[params.place]
    item = ITEMS[params.item]
    mission = MISSIONS[params.mission]
    approach = APPROACHES[params.approach]

    if approach.kindness < KINDNESS_MIN:
        raise StoryError(explain_approach_rejection(params.approach))
    if not item_matches_mission(item, mission) or mission.id not in place.supports:
        raise StoryError(explain_combo_rejection(params.place, item, mission))

    world = tell(
        place=place,
        item_cfg=item,
        mission=mission,
        approach=approach,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        borrower_name=params.borrower_name,
        borrower_gender=params.borrower_gender,
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

    py_combos = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if py_combos == clingo_combos:
        print(f"OK: valid_combos matches clingo ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_combos - py_combos:
            print("  only in clingo:", sorted(clingo_combos - py_combos))
        if py_combos - clingo_combos:
            print("  only in python:", sorted(py_combos - clingo_combos))

    py_approaches = {a.id for a in sensible_approaches()}
    clingo_approaches = set(asp_sensible_approaches())
    if py_approaches == clingo_approaches:
        print(f"OK: sensible approaches match ({sorted(py_approaches)}).")
    else:
        rc = 1
        print("MISMATCH in sensible approaches:")
        print("  clingo:", sorted(clingo_approaches))
        print("  python:", sorted(py_approaches))

    cases = list(CURATED)
    for s in range(40):
        try:
            args = build_parser().parse_args([])
            p = resolve_params(args, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        random_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        random_params.seed = 123
        smoke2 = generate(random_params)
        if not smoke2.story.strip():
            raise StoryError("(Random smoke test failed: generated empty story.)")
        print("OK: random smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_approach/1.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        approaches = asp_sensible_approaches()
        print(f"sensible approaches: {', '.join(approaches)}\n")
        print(f"{len(combos)} valid (place, item, mission) combos:\n")
        for place, item, mission in combos:
            print(f"  {place:10} {item:10} {mission}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.item} at {p.place} ({p.mission}, {p.approach}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
