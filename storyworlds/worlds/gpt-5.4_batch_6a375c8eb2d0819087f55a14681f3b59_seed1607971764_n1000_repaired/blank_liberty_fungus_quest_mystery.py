#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/blank_liberty_fungus_quest_mystery.py
================================================================

A standalone storyworld for a tiny mystery-quest domain: a child is given a
blank-looking clue card on Liberty Day, reveals its hidden words in a safe way,
follows a strange fungus mark, and finds a missing festival treasure.

The world prefers only combinations that make concrete sense:
- the reveal method must actually work for the chosen hidden clue card
- the setting must actually contain the final hiding place for the missing item

The story shape is always a complete little mystery:
premise -> blank clue -> fungus trail -> turn or detour -> discovery -> changed ending.
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
HASTY_TRAITS = {"hasty", "bold", "restless"}


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
class Setting:
    id: str
    label: str
    opening: str
    fungus_site: str
    fungus_detail: str
    final_spots: set[str] = field(default_factory=set)
    damp: bool = False
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
class ClueCard:
    id: str
    label: str
    hidden_words: str
    reveal: str
    reveal_text: str
    second_clue: str
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
class Prize:
    id: str
    label: str
    phrase: str
    spot: str
    ending_image: str
    spooky: bool = False
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

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_visible_clue(world: World) -> list[str]:
    card = world.get("card")
    if card.meters["revealed"] < THRESHOLD:
        return []
    sig = ("visible", "card")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    card.meters["visible"] += 1
    hero = world.get("hero")
    hero.memes["curiosity"] += 1
    return []


def _r_fungus_notice(world: World) -> list[str]:
    marker = world.get("marker")
    if marker.meters["noticed"] < THRESHOLD:
        return []
    sig = ("fungus_notice", "marker")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    hero.memes["wonder"] += 1
    return []


def _r_find_prize(world: World) -> list[str]:
    prize = world.get("prize")
    if prize.meters["found"] < THRESHOLD:
        return []
    sig = ("found", "prize")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    helper.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="visible_clue", tag="physical", apply=_r_visible_clue),
    Rule(name="fungus_notice", tag="perception", apply=_r_fungus_notice),
    Rule(name="find_prize", tag="resolution", apply=_r_find_prize),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reveal_works(card: ClueCard, reveal: str) -> bool:
    return card.reveal == reveal


def prize_fits(setting: Setting, prize: Prize) -> bool:
    return prize.spot in setting.final_spots


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid, card in CLUES.items():
            for rid in REVEALS:
                if not reveal_works(card, rid):
                    continue
                for pid, prize in PRIZES.items():
                    if prize_fits(setting, prize):
                        combos.append((sid, cid, rid, pid))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    prize = PRIZES[params.prize]
    if params.trait in HASTY_TRAITS and prize.spooky:
        return "detour"
    return "direct"


def predict_detour(trait: str, prize: Prize) -> bool:
    return trait in HASTY_TRAITS and prize.spooky


def introduce(world: World, hero: Entity, helper: Entity, prize: Prize) -> None:
    hero.memes["curiosity"] = 1.0
    helper.memes["calm"] = 1.0
    world.say(
        f"It was Liberty Day, and {world.setting.opening}."
    )
    world.say(
        f"{hero.id} had promised to help {helper.label_word} find {prize.phrase}, "
        f"which had gone missing before the afternoon celebration."
    )
    world.say(
        f'"Then it is a quest," {helper.label_word.capitalize()} said. '
        f'"And every good quest begins with a mystery."'
    )


def give_blank_card(world: World, hero: Entity, helper: Entity, card_cfg: ClueCard) -> None:
    card = world.get("card")
    hero.memes["wonder"] += 1
    world.say(
        f"{helper.label_word.capitalize()} slipped {hero.pronoun('object')} a small card. "
        f"It looked almost blank, as pale as a cloud."
    )
    world.say(
        f'"It cannot be truly blank," {hero.id} whispered. '
        f'"A mystery never starts with nothing."'
    )
    card.attrs["hidden_words"] = card_cfg.hidden_words
    card.attrs["second_clue"] = card_cfg.second_clue


def reveal_card(world: World, hero: Entity, card_cfg: ClueCard) -> None:
    card = world.get("card")
    card.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(card_cfg.reveal_text)
    world.say(
        f"Slowly, words rose on the card: {card_cfg.hidden_words!r}. "
        f"{hero.id}'s eyes grew round."
    )


def go_to_fungus(world: World, hero: Entity, helper: Entity) -> None:
    marker = world.get("marker")
    marker.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They followed the clue to {world.setting.fungus_site}. "
        f"There, {world.setting.fungus_detail}"
    )
    world.say(
        f'"There is the fungus mark," {helper.label_word} murmured. '
        f'"Someone wanted sharp eyes to find it."'
    )
    hero.memes["curiosity"] += 1


def wrong_turn(world: World, hero: Entity, helper: Entity, prize: Prize) -> None:
    hero.memes["worry"] += 1
    hero.meters["wrong_turn"] += 1
    world.say(
        f"The shadows around the {prize.spot} looked deep, and {hero.id} hurried ahead too fast."
    )
    world.say(
        f"For a moment, the quest felt spooky instead of exciting. "
        f"{hero.id} chose the wrong corner and found only dust and old leaves."
    )
    world.say(
        f'"Back up," said {helper.label_word} gently. '
        f'"Mysteries do not like rushing. Read the fungus clue again."'
    )


def read_second_clue(world: World, hero: Entity, card_cfg: ClueCard, prize: Prize) -> None:
    world.say(
        f"Behind the fungus mark, tucked in a crack, they found a second scrap of paper. "
        f"It said, {card_cfg.second_clue!r}."
    )
    world.say(
        f"Now the path was clear: the missing thing was waiting by the {prize.spot}."
    )


def find_prize(world: World, hero: Entity, helper: Entity, prize_cfg: Prize) -> None:
    prize = world.get("prize")
    prize.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they searched by the {prize_cfg.spot}, and {hero.id} gave a happy gasp."
    )
    world.say(
        f"There was {prize_cfg.phrase}, safe at last. Someone had tucked it away so carefully "
        f"that it had turned the morning into a little mystery."
    )


def close_story(world: World, hero: Entity, helper: Entity, prize_cfg: Prize, outcome: str) -> None:
    if outcome == "detour":
        hero.memes["worry"] = 0.0
        world.say(
            f'{hero.id} laughed a soft, shaky laugh. "I thought the quest was getting too dark," '
            f"{hero.pronoun()} admitted."
        )
        world.say(
            f'"Only until we looked closely," said {helper.label_word}. '
            f'"A calm heart finds more than a quick one."'
        )
    else:
        world.say(
            f'"You solved it with patient eyes," {helper.label_word} said, giving {hero.id} a proud smile.'
        )
    world.say(
        f"When they carried the treasure back, the whole place seemed brighter. {prize_cfg.ending_image}"
    )
    world.say(
        f"After that, whenever {hero.id} saw something blank, {hero.pronoun()} no longer thought it meant empty. "
        f"It might only mean that a mystery was waiting to be seen."
    )
def tell(
    clue: Clue,
    reveal: Reveal,
    prize_cfg: Prize,
    hero_name: str,
    hero_type: HeroType,
    helper_type: HelperType,
    trait: Trait,
    setting=None,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, attrs={"trait": trait}))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_type))
    card = world.add(Entity(id="card", type="card", label=clue.label))
    marker = world.add(Entity(id="marker", type="fungus", label="fungus mark"))
    prize = world.add(Entity(id="prize", type="prize", label=prize_cfg.label, attrs={"spot": prize_cfg.spot}))

    world.facts["hero_name"] = hero_name
    world.facts["trait"] = trait
    world.facts["outcome"] = outcome_of(StoryParams(
        setting=setting.id,
        clue=clue.id,
        reveal=reveal,
        prize=prize_cfg.id,
        hero=hero_name,
        gender=hero_type,
        helper=helper_type,
        trait=trait,
        seed=None,
    ))
    world.facts["detour_predicted"] = predict_detour(trait, prize_cfg)

    introduce(world, hero, helper, prize_cfg)
    world.para()
    give_blank_card(world, hero, helper, clue)
    reveal_card(world, hero, clue)
    world.para()
    go_to_fungus(world, hero, helper)
    if predict_detour(trait, prize_cfg):
        wrong_turn(world, hero, helper, prize_cfg)
    read_second_clue(world, hero, clue, prize_cfg)
    world.para()
    find_prize(world, hero, helper, prize_cfg)
    close_story(world, hero, helper, prize_cfg, world.facts["outcome"])

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        setting=setting,
        prize_cfg=prize_cfg,
        reveal=reveal,
        blank_card=True,
        fungus_seen=marker.meters["noticed"] >= THRESHOLD,
        revealed=card.meters["visible"] >= THRESHOLD,
        found=prize.meters["found"] >= THRESHOLD,
        wrong_turn=hero.meters["wrong_turn"] >= THRESHOLD,
    )
    return world
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


SETTINGS = {
    "orchard": Setting(
        id="orchard",
        label="the orchard",
        opening="the orchard was silver with morning dew, and little flags for Liberty Day fluttered between the trees",
        fungus_site="an old apple stump at the far edge of the path",
        fungus_detail="a fan of pale fungus curled from the wood like tiny shelves",
        final_spots={"birdhouse", "crate"},
        damp=True,
        tags={"orchard", "fungus"},
    ),
    "conservatory": Setting(
        id="conservatory",
        label="the glass conservatory",
        opening="the glass conservatory glowed green, and ribbons for Liberty Day hung between the warm windows",
        fungus_site="a cracked clay pot under the fern table",
        fungus_detail="a soft patch of white fungus dusted the broken rim",
        final_spots={"bench", "watering_can"},
        damp=True,
        tags={"conservatory", "fungus"},
    ),
    "museum_yard": Setting(
        id="museum_yard",
        label="the museum yard",
        opening="the museum yard was quiet before the crowd came, and a painted Liberty banner waited by the gate",
        fungus_site="the shaded stones behind the old bell wagon",
        fungus_detail="a neat crescent of fungus shone between the stones",
        final_spots={"wagon", "bench"},
        damp=False,
        tags={"museum", "fungus", "liberty"},
    ),
}

CLUES = {
    "sun_ink": ClueCard(
        id="sun_ink",
        label="sun-ink card",
        hidden_words="Seek the fungus sign where dew keeps secrets.",
        reveal="sunlight",
        reveal_text="They held the card in a stripe of sunlight, and faint brown letters woke on the blank paper.",
        second_clue="Look where the little roof keeps watch.",
        tags={"blank", "clue", "sunlight"},
    ),
    "pencil_rubbing": ClueCard(
        id="pencil_rubbing",
        label="raised-letter card",
        hidden_words="Shade the blank card and the path will speak.",
        reveal="pencil",
        reveal_text="Helper laid a soft pencil on its side and rubbed gently. Hidden letters climbed out of the blank card like a whisper.",
        second_clue="Search the seat where waiting feet grow still.",
        tags={"blank", "clue", "pencil"},
    ),
    "warm_breath": ClueCard(
        id="warm_breath",
        label="fog card",
        hidden_words="Breathe on the blank and follow the fungus crescent.",
        reveal="breath",
        reveal_text="They breathed warm air onto the card, and mist kissed the paper. For a moment the blank surface darkened, and silver words appeared.",
        second_clue="Find the thing tucked beside the tallest can.",
        tags={"blank", "clue", "breath"},
    ),
}

REVEALS = {
    "sunlight": "sunlight",
    "pencil": "pencil",
    "breath": "breath",
}

PRIZES = {
    "bell_ribbon": Prize(
        id="bell_ribbon",
        label="liberty ribbon",
        phrase="the blue liberty ribbon for the old bell",
        spot="bench",
        ending_image="The ribbon fluttered from Helper's hands like a small piece of sky.",
        spooky=False,
        tags={"liberty", "ribbon"},
    ),
    "parade_badge": Prize(
        id="parade_badge",
        label="liberty badge",
        phrase="the brass liberty badge for the parade leader",
        spot="birdhouse",
        ending_image="The little badge flashed in the light, bright and brave again.",
        spooky=False,
        tags={"liberty", "badge"},
    ),
    "lantern_key": Prize(
        id="lantern_key",
        label="lantern key",
        phrase="the tiny key that opened the Liberty lantern wagon",
        spot="wagon",
        ending_image="Soon the lantern wagon would shine all down the path.",
        spooky=False,
        tags={"liberty", "lantern"},
    ),
    "crate_medal": Prize(
        id="crate_medal",
        label="liberty medal",
        phrase="the paper liberty medal for the opening song",
        spot="crate",
        ending_image="The medal lay flat and safe, ready to swing on its red string.",
        spooky=True,
        tags={"liberty", "medal"},
    ),
    "can_token": Prize(
        id="can_token",
        label="garden token",
        phrase="the little liberty token tied to the watering cans",
        spot="watering_can",
        ending_image="Even the damp leaves seemed to nod when they carried it away.",
        spooky=True,
        tags={"liberty", "token"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Theo", "Ben", "Max", "Eli", "Noah", "Finn"]
TRAITS = ["careful", "curious", "gentle", "hasty", "bold", "restless"]
HELPERS = ["grandfather", "grandmother", "aunt", "uncle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize_cfg"]
    setting = f["setting"]
    clue = f["clue"]
    return [
        f'Write a gentle mystery Quest for a 3-to-5-year-old that includes the words "blank", "liberty", and "fungus".',
        f"Tell a story about a {hero.type} named {f['hero_name']} who finds a blank clue card, follows a fungus mark in {setting.label}, and discovers {prize.phrase}.",
        f"Write a child-friendly mystery where a hidden message appears on a blank card, leading to a Liberty Day treasure and a calm, happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize_cfg"]
    clue = f["clue"]
    setting = f["setting"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['hero_name']} and {helper_word}, who went on a mystery quest together. "
            f"They were trying to find {prize.phrase} before Liberty Day began.",
        ),
        (
            "Why did the card seem important even though it looked blank?",
            f"The card only looked blank at first, but hidden words were waiting inside it. "
            f"That made it the first clue in the mystery quest.",
        ),
        (
            f"How did they reveal the hidden message on the blank card?",
            f"They used {f['reveal']} to make the words appear. "
            f"That worked because this kind of clue card was made to show its message that way.",
        ),
        (
            "What did the fungus clue do in the story?",
            f"The fungus mark showed them the right place to stop and look closely. "
            f"It turned an ordinary corner of {setting.label} into the middle of the mystery.",
        ),
    ]
    if f["wrong_turn"]:
        qa.append((
            f"Did {f['hero_name']} solve the quest right away?",
            f"No. {f['hero_name']} hurried when the place felt spooky and took a wrong turn first. "
            f"Then {helper_word} helped {hero.pronoun('object')} slow down, reread the clue, and find the right path.",
        ))
    else:
        qa.append((
            f"Did {f['hero_name']} solve the quest right away?",
            f"Yes. {f['hero_name']} stayed patient and followed each clue carefully. "
            f"That helped {hero.pronoun('object')} reach the hiding place without getting lost.",
        ))
    qa.append((
        "How did the story end?",
        f"They found {prize.phrase} and carried it back in time for Liberty Day. "
        f"The ending shows that the mystery was solved and the celebration could begin happily.",
    ))
    return qa


KNOWLEDGE = {
    "blank": [
        (
            "What does blank mean?",
            "Blank means something looks empty or has no writing on it yet. Sometimes a blank page is truly empty, and sometimes it is hiding something you cannot see at first.",
        )
    ],
    "liberty": [
        (
            "What does liberty mean?",
            "Liberty means freedom. It is a word people use when they talk about being free to live, speak, and choose fairly.",
        )
    ],
    "fungus": [
        (
            "What is fungus?",
            "Fungus is a living thing that can grow in damp places, like on wood, soil, or old leaves. Mushrooms are one kind of fungus.",
        )
    ],
    "sunlight": [
        (
            "Why can sunlight help you see hidden things?",
            "Strong light can make faint marks easier to notice. Sometimes a shiny or dried message shows up better when sunlight passes through the paper.",
        )
    ],
    "pencil": [
        (
            "How can a pencil rubbing show hidden letters?",
            "If letters are raised or pressed into paper, a soft pencil rubbed over the top can darken the high places and make the shapes easier to see.",
        )
    ],
    "breath": [
        (
            "Why would warm breath change a piece of paper for a moment?",
            "Warm breath carries tiny drops of water. Those drops can make some marks show up for a little while before the paper dries again.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle with missing information that you have to figure out. You solve it by noticing clues and thinking carefully.",
        )
    ],
}

KNOWLEDGE_ORDER = ["blank", "liberty", "fungus", "sunlight", "pencil", "breath", "mystery"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"blank", "liberty", "fungus", "mystery", f["reveal"]}
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if attrs:
            parts.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    setting: str
    clue: str
    reveal: str
    prize: str
    hero: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        setting="orchard",
        clue="sun_ink",
        reveal="sunlight",
        prize="parade_badge",
        hero="Nora",
        gender="girl",
        helper="grandfather",
        trait="careful",
        seed=1,
    ),
    StoryParams(
        setting="conservatory",
        clue="warm_breath",
        reveal="breath",
        prize="can_token",
        hero="Ben",
        gender="boy",
        helper="aunt",
        trait="hasty",
        seed=2,
    ),
    StoryParams(
        setting="museum_yard",
        clue="pencil_rubbing",
        reveal="pencil",
        prize="lantern_key",
        hero="Eli",
        gender="boy",
        helper="grandmother",
        trait="curious",
        seed=3,
    ),
    StoryParams(
        setting="orchard",
        clue="sun_ink",
        reveal="sunlight",
        prize="crate_medal",
        hero="Lily",
        gender="girl",
        helper="uncle",
        trait="bold",
        seed=4,
    ),
]


def explain_reveal(clue: ClueCard, reveal: str) -> str:
    return (
        f"(No story: {clue.label} does not reveal with {reveal}. "
        f"It needs {clue.reveal}, so the hidden words can appear honestly.)"
    )


def explain_prize(setting: Setting, prize: Prize) -> str:
    spots = ", ".join(sorted(setting.final_spots))
    return (
        f"(No story: {prize.phrase} cannot be hidden in {setting.label}. "
        f"This setting supports these hiding places: {spots}.)"
    )


ASP_RULES = r"""
works(C, R) :- clue(C), clue_reveal(C, R).
fits(S, P) :- setting(S), prize(P), prize_spot(P, Spot), setting_spot(S, Spot).
valid(S, C, R, P) :- setting(S), clue(C), reveal(R), prize(P), works(C, R), fits(S, P).

hasty_trait(T) :- trait_name(T), is_hasty(T).
detour :- chosen_trait(T), hasty_trait(T), chosen_prize(P), spooky(P).
outcome(detour) :- detour.
outcome(direct) :- not detour.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in sorted(setting.final_spots):
            lines.append(asp.fact("setting_spot", sid, spot))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_reveal", cid, clue.reveal))
    for rid in REVEALS:
        lines.append(asp.fact("reveal", rid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_spot", pid, prize.spot))
        if prize.spooky:
            lines.append(asp.fact("spooky", pid))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(HASTY_TRAITS):
        lines.append(asp.fact("is_hasty", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_prize", params.prize),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(20):
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
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        sink = io.StringIO()
        with redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a blank clue, a fungus trail, and a Liberty Day mystery quest."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.reveal and not reveal_works(CLUES[args.clue], args.reveal):
        raise StoryError(explain_reveal(CLUES[args.clue], args.reveal))
    if args.setting and args.prize and not prize_fits(SETTINGS[args.setting], PRIZES[args.prize]):
        raise StoryError(explain_prize(SETTINGS[args.setting], PRIZES[args.prize]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.clue is None or combo[1] == args.clue)
        and (args.reveal is None or combo[2] == args.reveal)
        and (args.prize is None or combo[3] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, clue, reveal, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        clue=clue,
        reveal=reveal,
        prize=prize,
        hero=hero,
        gender=gender,
        helper=helper,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.reveal not in REVEALS:
        raise StoryError(f"(Unknown reveal method: {params.reveal})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    prize = PRIZES[params.prize]

    if not reveal_works(clue, params.reveal):
        raise StoryError(explain_reveal(clue, params.reveal))
    if not prize_fits(setting, prize):
        raise StoryError(explain_prize(setting, prize))

    world = tell(
        setting=setting,
        clue=clue,
        reveal=params.reveal,
        prize_cfg=prize,
        hero_name=params.hero,
        hero_type=params.gender,
        helper_type=params.helper,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    text = sample.story
    hero_name = sample.params.hero
    text = text.replace("hero", hero_name)
    text = text.replace("Helper", sample.world.get("helper").label_word.capitalize() if sample.world else "Helper")
    if header:
        print(header)
    print(text)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, reveal, prize) combos:\n")
        for setting, clue, reveal, prize in combos:
            print(f"  {setting:13} {clue:15} {reveal:8} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.hero}: {p.setting}, {p.clue}, {p.prize} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
