#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/meter_wilderness_curiosity_detective_story.py
========================================================================

A standalone story world for a tiny detective tale set at a wilderness camp.

Premise
-------
A curious child notices that an important camp item is missing and treats the
problem like a small detective case. The child studies one grounded clue, follows
it through the wilderness, and solves the mystery.

This world keeps the logic tight:
- each missing item only allows causes that make ordinary sense,
- each cause has the clue and hiding place it naturally produces,
- the prose follows the simulated state rather than swapping nouns into one fixed
  paragraph,
- every story mentions the creek's painted meter board and the wilderness camp.

Run it
------
    python storyworlds/worlds/gpt-5.4/meter_wilderness_curiosity_detective_story.py
    python storyworlds/worlds/gpt-5.4/meter_wilderness_curiosity_detective_story.py --item whistle --cause raven
    python storyworlds/worlds/gpt-5.4/meter_wilderness_curiosity_detective_story.py --item berry_basket --cause wind
    python storyworlds/worlds/gpt-5.4/meter_wilderness_curiosity_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/meter_wilderness_curiosity_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/meter_wilderness_curiosity_detective_story.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ranger_woman"}
        male = {"boy", "father", "man", "ranger_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Item:
    id: str
    label: str
    phrase: str
    article: str
    light: bool = False
    edible: bool = False
    shiny: bool = False
    papery: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.article[0].upper() + self.article[1:]
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
class Cause:
    id: str
    agent: str
    reason: str
    place: str
    clue: str
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
class Clue:
    id: str
    label: str
    notice: str
    meaning: str
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
class Place:
    id: str
    label: str
    phrase: str
    found_text: str
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
class Helper:
    id: str
    name: str
    type: str
    role_word: str
    style: str
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


def _r_missing_case(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["missing"] >= THRESHOLD:
        sig = ("missing_case",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["curiosity"] += 1
            hero.memes["worry"] += 1
            out.append("__missing__")
    return out


def _r_notice_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    clue = world.get("clue")
    if clue.meters["noticed"] >= THRESHOLD:
        sig = ("noticed",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["focus"] += 1
            hero.memes["confidence"] += 1
            out.append("__noticed__")
    return out


def _r_found_item(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["found"] >= THRESHOLD:
        sig = ("found",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            hero.memes["joy"] += 1
            hero.memes["pride"] += 1
            out.append("__found__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_case", tag="emotional", apply=_r_missing_case),
    Rule(name="notice_clue", tag="cognitive", apply=_r_notice_clue),
    Rule(name="found_item", tag="emotional", apply=_r_found_item),
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


ITEMS = {
    "map": Item(
        id="map",
        label="trail map",
        phrase="a folded trail map",
        article="the trail map",
        papery=True,
        light=True,
        tags={"map", "paper"},
    ),
    "sketchbook": Item(
        id="sketchbook",
        label="sketchbook",
        phrase="a little sketchbook",
        article="the sketchbook",
        papery=True,
        light=True,
        tags={"paper", "drawing"},
    ),
    "whistle": Item(
        id="whistle",
        label="silver whistle",
        phrase="a silver whistle",
        article="the silver whistle",
        shiny=True,
        light=True,
        tags={"whistle", "shiny"},
    ),
    "berry_basket": Item(
        id="berry_basket",
        label="berry basket",
        phrase="a berry basket",
        article="the berry basket",
        edible=True,
        tags={"berries", "food"},
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        agent="the wind",
        reason="a gust lifted it and carried it off",
        place="creek_meter",
        clue="flutter_strip",
        tags={"wind"},
    ),
    "raven": Cause(
        id="raven",
        agent="a raven",
        reason="the bird liked the bright, shiny thing",
        place="pine_stump",
        clue="black_feather",
        tags={"bird"},
    ),
    "squirrel": Cause(
        id="squirrel",
        agent="a squirrel",
        reason="the smell of berries drew it close",
        place="log_hollow",
        clue="nut_shells",
        tags={"animal", "food"},
    ),
    "guide_tidied": Cause(
        id="guide_tidied",
        agent="the camp guide",
        reason="the guide had tucked it away to keep the table neat",
        place="guide_satchel",
        clue="green_tag",
        tags={"adult", "tidy"},
    ),
}

CLUES = {
    "flutter_strip": Clue(
        id="flutter_strip",
        label="a tiny strip of paper fluttering on a branch",
        notice="A tiny strip of paper fluttered from a branch near the path.",
        meaning="It looked torn from something light enough for the wind to snatch.",
        tags={"paper", "wind"},
    ),
    "black_feather": Clue(
        id="black_feather",
        label="a glossy black feather",
        notice="A glossy black feather lay beside the camp table.",
        meaning="That was the sort of clue a sharp-eyed detective would tie to a curious bird.",
        tags={"bird", "feather"},
    ),
    "nut_shells": Clue(
        id="nut_shells",
        label="a scatter of cracked nut shells",
        notice="A scatter of cracked nut shells sat beside a ferny root.",
        meaning="Small woodland teeth had been busy there, which pointed away from people and toward an animal.",
        tags={"animal", "squirrel"},
    ),
    "green_tag": Clue(
        id="green_tag",
        label="a neat green tag from the guide's satchel",
        notice="A neat green tag had slipped loose near the picnic table leg.",
        meaning="It matched the guide's satchel, which meant careful hands, not sneaky paws, had moved the item.",
        tags={"adult", "tidy"},
    ),
}

PLACES = {
    "creek_meter": Place(
        id="creek_meter",
        label="the creek meter board",
        phrase="the painted meter board by the creek",
        found_text="It was hooked gently over the top rung of the creek meter board, safe but damp with mist.",
        tags={"meter", "creek"},
    ),
    "pine_stump": Place(
        id="pine_stump",
        label="the old pine stump",
        phrase="the old pine stump beyond the ferns",
        found_text="It rested on the pine stump as if a proud bird had set out a trophy.",
        tags={"woods", "bird"},
    ),
    "log_hollow": Place(
        id="log_hollow",
        label="the hollow log",
        phrase="the hollow log near the berry patch",
        found_text="It sat just inside the hollow log, with a few berries missing and purple juice on the bark.",
        tags={"woods", "animal"},
    ),
    "guide_satchel": Place(
        id="guide_satchel",
        label="the guide's satchel",
        phrase="the guide's canvas satchel on the bench",
        found_text="It was tucked inside the satchel in a careful dry pocket.",
        tags={"camp", "bag"},
    ),
}

HELPERS = {
    "cousin_ivy": Helper(
        id="cousin_ivy",
        name="Ivy",
        type="girl",
        role_word="cousin",
        style="quietly noticed small things",
        tags={"child_helper"},
    ),
    "friend_joel": Helper(
        id="friend_joel",
        name="Joel",
        type="boy",
        role_word="friend",
        style="asked blunt, useful questions",
        tags={"child_helper"},
    ),
    "ranger_mara": Helper(
        id="ranger_mara",
        name="Ranger Mara",
        type="ranger_woman",
        role_word="ranger",
        style="knew the paths better than anyone",
        tags={"adult_helper"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Ava", "Mia", "Rose", "Tessa"]
BOY_NAMES = ["Ben", "Theo", "Max", "Sam", "Eli", "Finn"]


def item_allows_cause(item: Item, cause: Cause) -> bool:
    if cause.id == "wind":
        return item.light or item.papery
    if cause.id == "raven":
        return item.shiny or item.light
    if cause.id == "squirrel":
        return item.edible
    if cause.id == "guide_tidied":
        return True
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for item_id, item in ITEMS.items():
        for cause_id, cause in CAUSES.items():
            clue_id = cause.clue
            place_id = cause.place
            if item_allows_cause(item, cause):
                combos.append((item_id, cause_id, clue_id, place_id))
    return sorted(combos)


def explain_rejection(item: Item, cause: Cause) -> str:
    if cause.id == "wind":
        return (
            f"(No story: {item.article} is not the kind of light paper-like thing a gust would carry away. "
            f"Pick a lighter item such as a map or sketchbook.)"
        )
    if cause.id == "raven":
        return (
            f"(No story: {item.article} gives a raven no ordinary reason to snatch it. "
            f"Choose something shiny or easy to lift, such as a whistle.)"
        )
    if cause.id == "squirrel":
        return (
            f"(No story: {item.article} is not food, so a squirrel would not drag it into the wilderness. "
            f"Choose the berry basket for that cause.)"
        )
    return "(No story: that cause does not fit the missing item.)"


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} loved mysteries so much that even a walk through the wilderness felt like the start of a detective story. "
        f"At camp, {helper.id}, {hero.pronoun('possessive')} {helper.attrs['role_word']}, was the usual assistant and {helper.attrs['style']}."
    )
    world.say(
        "Beyond the cabins, a creek slipped over stones, and beside it stood a painted meter board that the rangers used to watch the water."
    )


def camp_setup(world: World, hero: Entity, guide: Entity, item_cfg: Item) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"That morning, the camp guide had set out {item_cfg.phrase} on the long table for the trail game."
    )
    world.say(
        f"{hero.id} touched the edge of {item_cfg.article} and promised to keep watch over the whole case, just in case a mystery came looking."
    )
    world.facts["guide_name"] = guide.id


def discover_missing(world: World, hero: Entity, item: Entity, item_cfg: Item) -> None:
    item.meters["missing"] = 1.0
    propagate(world, narrate=False)
    mood = "a cold little mystery" if hero.memes["worry"] >= THRESHOLD else "a puzzle"
    world.say(
        f"But when the game was ready to begin, {item_cfg.article} was gone. The empty place on the table gave {hero.id} {mood} right in the middle of breakfast."
    )
    world.say(
        f'"Detective work," {hero.id} whispered. "{item_cfg.The} did not just walk away."'
    )


def inspect_table(world: World, hero: Entity, helper: Entity, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} bent low beside the table while {helper.id} stood very still like a proper assistant."
    )
    world.say(clue_cfg.notice)
    world.say(clue_cfg.meaning)


def reason_out(world: World, hero: Entity, helper: Entity, cause_cfg: Cause, place_cfg: Place) -> None:
    focused = "Curiosity made the pieces click together" if hero.memes["focus"] >= THRESHOLD else "Slowly the pieces fit"
    world.say(
        f"{focused}. {hero.id} pointed toward {place_cfg.phrase} and said that {cause_cfg.agent} must have been involved."
    )
    if helper.type.startswith("ranger"):
        world.say(
            f'{helper.id} smiled. "Lead the way, detective," {helper.pronoun()} said.'
        )
    else:
        world.say(
            f'"Then we look there first," {helper.id} said, already trotting after {hero.pronoun("object")}.'
        )


def search_place(world: World, hero: Entity, place_cfg: Place) -> None:
    place = world.get("place")
    place.meters["searched"] = 1.0
    if place_cfg.id == "creek_meter":
        world.say(
            f"They followed the path through damp grass until the creek began talking over the stones. The painted meter board leaned beside the water like a tall striped witness."
        )
    elif place_cfg.id == "pine_stump":
        world.say(
            "They crossed a patch of soft needles where the pines made green shadows over the trail."
        )
    elif place_cfg.id == "log_hollow":
        world.say(
            "They pushed through ferns until the trees opened around an old fallen log with a dark hollow in its side."
        )
    else:
        world.say(
            "They hurried back to the bench where the guide's satchel rested beside a coil of rope."
        )


def recover(world: World, hero: Entity, item: Entity, item_cfg: Item, cause_cfg: Cause, place_cfg: Place) -> None:
    item.meters["found"] = 1.0
    item.meters["missing"] = 0.0
    propagate(world, narrate=False)
    if cause_cfg.id == "wind":
        item.meters["damp"] += 1
    elif cause_cfg.id == "raven":
        item.meters["scuffed"] += 1
    elif cause_cfg.id == "squirrel":
        item.meters["nibbled"] += 1
    world.say(place_cfg.found_text)
    world.say(
        f"{item_cfg.The} was found. {hero.id} solved the case by following one small clue all the way to the truth."
    )


def explain_solution(world: World, hero: Entity, guide: Entity, item_cfg: Item, cause_cfg: Cause) -> None:
    if cause_cfg.id == "guide_tidied":
        world.say(
            f'Soon {guide.id} laughed softly and admitted that {guide.pronoun()} had moved it to keep the breakfast table from getting crowded.'
        )
    else:
        world.say(
            f"{hero.id} explained that {cause_cfg.reason}, and everyone agreed the clue had said so from the start."
        )
    if world.get("item").meters["nibbled"] >= THRESHOLD:
        world.say(
            "A few berries were missing, but the basket itself was still safe enough for the game."
        )
    elif world.get("item").meters["damp"] >= THRESHOLD:
        world.say(
            "It was a little damp, so they spread it in the sun for a minute before using it."
        )
    elif world.get("item").meters["scuffed"] >= THRESHOLD:
        world.say(
            "The whistle had one tiny scrape, yet it still gave a bright clear note."
        )


def close_case(world: World, hero: Entity, helper: Entity, item_cfg: Item, place_cfg: Place) -> None:
    hero.memes["lesson"] += 1
    proud = "proud and calm" if hero.memes["pride"] >= THRESHOLD else "glad"
    world.say(
        f"After that, nobody hurried past odd little signs again. {hero.id} felt {proud}, because curiosity had turned worry into an answer."
    )
    world.say(
        f"By afternoon, {item_cfg.article} was back where it belonged, and {hero.id} and {helper.id} walked past {place_cfg.label} feeling like the finest detectives in the whole wilderness."
    )


def tell(
    item_cfg: Item,
    cause_cfg: Cause,
    clue_cfg: Clue,
    place_cfg: Place,
    helper_cfg: Helper,
    hero_name: str = "Nora",
    hero_type: str = "girl",
    guide_type: str = "ranger_woman",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    hero.id = hero_name
    helper = world.add(Entity(id=helper_cfg.name, kind="character", type=helper_cfg.type, label=helper_cfg.name))
    helper.attrs["role_word"] = helper_cfg.role_word
    helper.attrs["style"] = helper_cfg.style
    guide_name = "Ranger Sol" if guide_type == "ranger_man" else "Ranger Ada"
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, label=guide_name))
    item = world.add(Entity(id="item", type="item", label=item_cfg.label))
    clue = world.add(Entity(id="clue", type="clue", label=clue_cfg.label))
    place = world.add(Entity(id="place", type="place", label=place_cfg.label))
    guide.memes["care"] = 1.0
    hero.memes["curiosity"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["focus"] = 0.0
    hero.memes["confidence"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["lesson"] = 0.0
    item.meters["missing"] = 0.0
    item.meters["found"] = 0.0
    clue.meters["noticed"] = 0.0
    place.meters["searched"] = 0.0

    introduce(world, hero, helper)
    camp_setup(world, hero, guide, item_cfg)

    world.para()
    discover_missing(world, hero, item, item_cfg)
    inspect_table(world, hero, helper, clue_cfg)
    reason_out(world, hero, helper, cause_cfg, place_cfg)

    world.para()
    search_place(world, hero, place_cfg)
    recover(world, hero, item, item_cfg, cause_cfg, place_cfg)
    explain_solution(world, hero, guide, item_cfg, cause_cfg)

    world.para()
    close_case(world, hero, helper, item_cfg, place_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        guide=guide,
        item_cfg=item_cfg,
        cause_cfg=cause_cfg,
        clue_cfg=clue_cfg,
        place_cfg=place_cfg,
        item=item,
        clue=clue,
        place=place,
        solved=item.meters["found"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    cause = f["cause_cfg"]
    return [
        f'Write a detective story for a 3-to-5-year-old about a curious child in the wilderness who notices that {item.article} is missing.',
        f'Write a gentle mystery where {hero.id} solves a small camp case by following one clue and thinking carefully. Include the word "meter".',
        f"Tell a child-facing camp detective story where the missing object turns out to involve {cause.agent} and the ending feels calm and clever.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    guide = f["guide"]
    item_cfg = f["item_cfg"]
    cause = f["cause_cfg"]
    clue = f["clue_cfg"]
    place = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a curious child at camp, and {helper.id}, the helper in the little detective case. They were at a wilderness camp where a missing object became a mystery."
        ),
        (
            f"What was missing?",
            f"{item_cfg.The} was missing from the camp table. That empty place is what made {hero.id} start investigating."
        ),
        (
            f"What clue did {hero.id} find?",
            f"{hero.id} found {clue.label}. That clue mattered because it pointed toward {cause.agent}, not a wild guess."
        ),
        (
            f"How did {hero.id} solve the case?",
            f"{hero.id} slowed down, studied the clue, and followed it to {place.phrase}. The case was solved by careful noticing, not by guessing."
        ),
        (
            f"Why did the clue point to {cause.agent}?",
            f"{clue.meaning} That is why {hero.id} chose the right place to search."
        ),
    ]
    if cause.id == "guide_tidied":
        qa.append(
            (
                f"Was anyone being mean when {item_cfg.article} went missing?",
                f"No. {guide.id} had moved it while tidying up, so the mystery was about a misunderstanding, not a bad trick. The clue showed that careful hands had moved it."
            )
        )
    else:
        qa.append(
            (
                f"What had really happened to {item_cfg.article}?",
                f"{cause.agent.capitalize()} had taken or moved it. {hero.id} could explain that because the clue matched what had happened."
            )
        )
    ending = "curiosity had turned worry into an answer"
    qa.append(
        (
            "How did the story end?",
            f"The missing item was found and returned, and {hero.id} felt proud. The final feeling was that {ending}."
        )
    )
    return qa


KNOWLEDGE = {
    "meter": [
        (
            "What is a meter board by a creek?",
            "A meter board is a marked board people use to see how high the water is. Rangers can glance at it and tell whether the creek is low or high."
        )
    ],
    "wilderness": [
        (
            "What is wilderness?",
            "Wilderness is a natural place with trees, plants, rocks, and animals where much of the land is still wild. People visit it carefully and try not to disturb it."
        )
    ],
    "feather": [
        (
            "What can a feather tell you?",
            "A feather can be a clue that a bird was nearby. Detectives and trackers use small signs like that to guess what passed through a place."
        )
    ],
    "wind": [
        (
            "Can wind move things?",
            "Yes, wind can blow light things like paper or leaves from one place to another. The lighter the thing is, the easier it is for a gust to carry it."
        )
    ],
    "squirrel": [
        (
            "Why would a squirrel take food?",
            "A squirrel looks for food it can carry and hide. If it smells berries or nuts, it may drag them to a safer place to eat."
        )
    ],
    "raven": [
        (
            "Why might a raven pick up a shiny thing?",
            "Ravens are curious birds and sometimes investigate bright or unusual objects. A shiny little thing can catch a raven's eye."
        )
    ],
    "map": [
        (
            "What does a trail map do?",
            "A trail map shows paths and places so people know where to go. It helps walkers stay on the right trail."
        )
    ],
    "whistle": [
        (
            "What is a whistle for at camp?",
            "A whistle makes a loud sound that carries far. At camp it can help people signal to one another."
        )
    ],
    "berries": [
        (
            "Why are berries tempting to animals?",
            "Berries smell sweet and taste good to many animals. That is why food should be watched carefully outside."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and uses them to figure out what happened. Good detectives notice details before they decide."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "detective",
    "meter",
    "wilderness",
    "wind",
    "feather",
    "raven",
    "squirrel",
    "map",
    "whistle",
    "berries",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "meter", "wilderness"} | set(f["cause_cfg"].tags) | set(f["clue_cfg"].tags) | set(f["item_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:14} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    item: str
    cause: str
    clue: str
    place: str
    helper: str
    hero: str
    gender: str
    guide: str
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
        item="map",
        cause="wind",
        clue="flutter_strip",
        place="creek_meter",
        helper="cousin_ivy",
        hero="Nora",
        gender="girl",
        guide="ranger_woman",
        seed=101,
    ),
    StoryParams(
        item="whistle",
        cause="raven",
        clue="black_feather",
        place="pine_stump",
        helper="friend_joel",
        hero="Ben",
        gender="boy",
        guide="ranger_man",
        seed=102,
    ),
    StoryParams(
        item="berry_basket",
        cause="squirrel",
        clue="nut_shells",
        place="log_hollow",
        helper="ranger_mara",
        hero="Lily",
        gender="girl",
        guide="ranger_woman",
        seed=103,
    ),
    StoryParams(
        item="sketchbook",
        cause="guide_tidied",
        clue="green_tag",
        place="guide_satchel",
        helper="friend_joel",
        hero="Theo",
        gender="boy",
        guide="ranger_man",
        seed=104,
    ),
]


ASP_RULES = r"""
valid(Item, Cause, Clue, Place) :-
    item(Item), cause(Cause), clue(Clue), place(Place),
    allows(Item, Cause),
    cause_clue(Cause, Clue),
    cause_place(Cause, Place).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.light:
            lines.append(asp.fact("light", item_id))
        if item.edible:
            lines.append(asp.fact("edible", item_id))
        if item.shiny:
            lines.append(asp.fact("shiny", item_id))
        if item.papery:
            lines.append(asp.fact("papery", item_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_clue", cause_id, cause.clue))
        lines.append(asp.fact("cause_place", cause_id, cause.place))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for item_id, item in ITEMS.items():
        for cause_id, cause in CAUSES.items():
            if item_allows_cause(item, cause):
                lines.append(asp.fact("allows", item_id, cause_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        sink = io.StringIO()
        stdout = sys.stdout
        try:
            sys.stdout = sink
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = stdout
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small wilderness detective storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["ranger_woman", "ranger_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.cause:
        item = ITEMS[args.item]
        cause = CAUSES[args.cause]
        if not item_allows_cause(item, cause):
            raise StoryError(explain_rejection(item, cause))
    if args.cause and args.clue and args.clue != CAUSES[args.cause].clue:
        raise StoryError(
            f"(No story: cause '{args.cause}' goes with clue '{CAUSES[args.cause].clue}', not '{args.clue}'.)"
        )
    if args.cause and args.place and args.place != CAUSES[args.cause].place:
        raise StoryError(
            f"(No story: cause '{args.cause}' leads to place '{CAUSES[args.cause].place}', not '{args.place}'.)"
        )
    if args.clue and args.place:
        matching = [c for c in CAUSES.values() if c.clue == args.clue and c.place == args.place]
        if not matching:
            raise StoryError("(No story: that clue does not naturally lead to that place.)")

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
        and (args.place is None or combo[3] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, cause_id, clue_id, place_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    guide = args.guide or rng.choice(["ranger_woman", "ranger_man"])
    return StoryParams(
        item=item_id,
        cause=cause_id,
        clue=clue_id,
        place=place_id,
        helper=helper,
        hero=hero,
        gender=gender,
        guide=guide,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.guide not in {"ranger_woman", "ranger_man"}:
        raise StoryError(f"(Unknown guide type: {params.guide})")

    item_cfg = ITEMS[params.item]
    cause_cfg = CAUSES[params.cause]
    if not item_allows_cause(item_cfg, cause_cfg):
        raise StoryError(explain_rejection(item_cfg, cause_cfg))
    if params.clue != cause_cfg.clue:
        raise StoryError(
            f"(Invalid story: cause '{params.cause}' requires clue '{cause_cfg.clue}', not '{params.clue}'.)"
        )
    if params.place != cause_cfg.place:
        raise StoryError(
            f"(Invalid story: cause '{params.cause}' requires place '{cause_cfg.place}', not '{params.place}'.)"
        )

    world = tell(
        item_cfg=item_cfg,
        cause_cfg=cause_cfg,
        clue_cfg=CLUES[params.clue],
        place_cfg=PLACES[params.place],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero,
        hero_type=params.gender,
        guide_type=params.guide,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, cause, clue, place) combos:\n")
        for item_id, cause_id, clue_id, place_id in combos:
            print(f"  {item_id:12} {cause_id:12} {clue_id:14} {place_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero}: {p.item} / {p.cause} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
