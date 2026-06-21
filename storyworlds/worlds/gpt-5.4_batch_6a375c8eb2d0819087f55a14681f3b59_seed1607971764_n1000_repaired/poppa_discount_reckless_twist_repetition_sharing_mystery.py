#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/poppa_discount_reckless_twist_repetition_sharing_mystery.py
=======================================================================================

A standalone story world about a little shop mystery: in the evening, discount
cards keep disappearing. A child helper and poppa follow repeated clues, fear a
reckless thief, and discover a twist: the secret mover was trying to share food
with someone who needed it.

Run it
------
python storyworlds/worlds/gpt-5.4/poppa_discount_reckless_twist_repetition_sharing_mystery.py
python storyworlds/worlds/gpt-5.4/poppa_discount_reckless_twist_repetition_sharing_mystery.py --item loaf --sharer neighbor_boy
python storyworlds/worlds/gpt-5.4/poppa_discount_reckless_twist_repetition_sharing_mystery.py --item cupcake
python storyworlds/worlds/gpt-5.4/poppa_discount_reckless_twist_repetition_sharing_mystery.py --all
python storyworlds/worlds/gpt-5.4/poppa_discount_reckless_twist_repetition_sharing_mystery.py --qa --json
python storyworlds/worlds/gpt-5.4/poppa_discount_reckless_twist_repetition_sharing_mystery.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandfather": "poppa", "grandmother": "gran"}.get(self.type, self.type)
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    clue: str
    clue_trace: str
    share_text: str
    servings: int
    can_discount: bool = True
    can_share: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def shareable(self) -> bool:
        return self.can_share and self.servings >= 2
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
class SharerCfg:
    id: str
    label: str
    type: str
    phrase: str
    reason: str
    needy_friend: str
    relation: str
    bold: int
    confesses_early: bool
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
class MethodCfg:
    id: str
    label: str
    sense: int
    boldness: int
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_mystery(world: World) -> list[str]:
    item = world.get("item")
    tag = world.get("tag")
    hero = world.get("hero")
    if tag.meters["moved"] < THRESHOLD:
        return []
    sig = ("mystery", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("shop").meters["mystery"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_sharing(world: World) -> list[str]:
    item = world.get("item")
    sharer = world.get("sharer")
    receiver = world.get("receiver")
    if item.meters["shared"] < THRESHOLD:
        return []
    sig = ("sharing", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sharer.memes["generosity"] += 1
    receiver.memes["relief"] += 1
    world.get("shop").memes["warmth"] += 1
    return []


def _r_guilt(world: World) -> list[str]:
    sharer = world.get("sharer")
    tag = world.get("tag")
    if tag.meters["moved"] < THRESHOLD:
        return []
    sig = ("guilt", sharer.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sharer.memes["worry"] += 1
    sharer.memes["guilt"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mystery", tag="social", apply=_r_mystery),
    Rule(name="sharing", tag="social", apply=_r_sharing),
    Rule(name="guilt", tag="emotional", apply=_r_guilt),
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
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(item: ItemCfg, method: MethodCfg) -> bool:
    return item.can_discount and item.shareable and method.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for item_id, item in ITEMS.items():
        for method_id, method in METHODS.items():
            if valid_combo(item, method):
                out.append((item_id, method_id))
    return sorted(out)


def outcome_of(params: "StoryParams") -> str:
    sharer = SHARERS[params.sharer]
    method = METHODS[params.method]
    if sharer.confesses_early:
        return "confession"
    if method.boldness >= 3 and sharer.bold >= 3:
        return "caught_in_act"
    return "kind_discovery"


def explain_item_rejection(item: ItemCfg) -> str:
    if not item.can_discount:
        return (
            f"(No story: {item.phrase} is not the sort of thing poppa would mark with a discount card here, "
            f"so there is no honest discount mystery.)"
        )
    if not item.shareable:
        return (
            f"(No story: {item.phrase} is too small to drive a sharing twist. "
            f"This world needs a food that can be split or passed on.)"
        )
    return "(No story: this item does not fit the shop mystery.)"


def explain_method_rejection(method: MethodCfg) -> str:
    return (
        f"(Refusing method '{method.id}': it is too unreasonable for this world "
        f"(sense={method.sense} < {SENSE_MIN}). The mystery may begin with a reckless act, "
        f"but the world refuses nonsense.)"
    )


def predict_need(world: World) -> dict:
    sim = world.copy()
    receiver = sim.get("receiver")
    receiver.meters["need"] += 1
    return {"need": receiver.meters["need"] >= THRESHOLD}


def introduce(world: World, hero: Entity, poppa: Entity) -> None:
    hero.memes["love"] += 1
    poppa.memes["calm"] += 1
    world.say(
        f"Every evening, {hero.id} helped {hero.pronoun('possessive')} poppa close the little corner shop. "
        f"When the lamps grew soft and gold, {poppa.label_word} straightened jars, folded paper sacks, "
        f"and let {hero.id} place the round discount cards on the foods that should be sold first."
    )


def show_item(world: World, hero: Entity, item: ItemCfg) -> None:
    world.say(
        f"That week, the most tempting thing on the shelf was {item.phrase}. "
        f"{hero.id} liked looking at the bright card beside it because the red circle seemed to whisper, "
        f'"Take me home before the night is over."'
    )


def first_vanish(world: World, item: ItemCfg) -> None:
    tag = world.get("tag")
    tag.meters["moved"] += 1
    world.get("item").meters["discounted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But on Monday, one discount card was gone. On Tuesday, another was gone. "
        f"On Wednesday, one more was gone. Each time, {item.label} still sat there, and each time "
        f"the empty space looked stranger than before."
    )


def worry(world: World, hero: Entity, poppa: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(
        f'"Poppa," {hero.id} whispered, "do we have a thief?"'
    )
    world.say(
        f'{poppa.label_word.capitalize()} rubbed his beard and looked around the quiet shop. '
        f'"Maybe. Or maybe we have a mystery that wants patient eyes."'
    )


def clue(world: World, item: ItemCfg) -> None:
    world.say(
        f"Near the shelf, {hero.id} found {item.clue}. It was not much, but it was the same kind of clue "
        f"every night, and repetition made it feel important."
    )
    world.facts["clue_seen"] = item.clue_trace


def suspect(world: World, hero: Entity, method: MethodCfg) -> None:
    hero.memes["suspicion"] += 1
    world.say(
        f"{hero.id} imagined a reckless somebody slipping in after the bell, {method.text}, "
        f"and touching things that did not belong to {hero.pronoun('object')}."
    )


def wait_and_watch(world: World, hero: Entity, poppa: Entity) -> None:
    world.say(
        f"So {hero.id} and {hero.pronoun('possessive')} poppa hid behind the flour bin and waited. "
        f"The clock ticked once, twice, three times. The shop felt full of breath and secrets."
    )


def move_tag(world: World, method: MethodCfg) -> None:
    tag = world.get("tag")
    tag.meters["moved"] += 1
    world.facts["method_text"] = method.text
    propagate(world, narrate=False)


def reveal_confession(world: World, sharer: Entity, receiver: Entity, item: ItemCfg) -> None:
    item_ent = world.get("item")
    item_ent.meters["shared"] += 1
    world.get("receiver").meters["need"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before anyone jumped out, {sharer.id} stopped all by {sharer.pronoun('object')}. "
        f'{sharer.pronoun().capitalize()} held the little card in one hand and said, '
        f'"I was going to tell you. {receiver.id} has had a thin supper all week, and {item.share_text}. '
        f'I thought if the price looked smaller, I could help."'
    )


def reveal_caught(world: World, hero: Entity, poppa: Entity, sharer: Entity, receiver: Entity,
                  item: ItemCfg, method: MethodCfg) -> None:
    item_ent = world.get("item")
    item_ent.meters["shared"] += 1
    world.get("receiver").meters["need"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last the door gave a tiny sigh, and in stepped {sharer.id}, {method.text}. "
        f"{hero.id} nearly gasped, because it was no wild stranger at all."
    )
    world.say(
        f'{poppa.label_word.capitalize()} lit the counter lamp, and the twist shone clear: '
        f'{sharer.id} was not trying to steal {item.label}. {sharer.pronoun().capitalize()} was moving the '
        f'discount card because {receiver.id} had had a thin supper all week, and {item.share_text}.'
    )


def gentle_talk(world: World, poppa: Entity, sharer: Entity, method: MethodCfg) -> None:
    sharer.memes["fear"] += 1
    world.say(
        f'{poppa.label_word.capitalize()} did not shout. He only held out his hand and said, '
        f'"Your heart was kind, but this was a reckless way to help. {method.label.capitalize()} without asking '
        f'makes a knot where trust should be."'
    )


def kind_fix(world: World, hero: Entity, poppa: Entity, sharer: Entity, receiver: Entity,
             item: ItemCfg) -> None:
    hero.memes["relief"] += 1
    sharer.memes["relief"] += 1
    poppa.memes["love"] += 1
    receiver.memes["hope"] += 1
    world.get("shop").meters["share_basket"] += 1
    world.say(
        f"Then {poppa.label_word} lifted a wicker basket from under the counter. "
        f'"If food should be shared, we will share it honestly," he said. '
        f'He set {item.phrase} inside the basket and added another one beside it.'
    )
    world.say(
        f"{hero.id} carried the basket with {sharer.id}, and together they brought it to {receiver.id}. "
        f"No one had to sneak. No one had to guess."
    )
    world.say(
        f"After that, each evening ended the same bright way: one card for sale, one basket for sharing, "
        f"and {hero.id} smiling whenever the shop bell rang."
    )


@dataclass
class StoryParams:
    item: str
    sharer: str
    method: str
    hero_name: str
    hero_type: str
    poppa_type: str
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


def tell(item: ItemCfg, sharer_cfg: SharerCfg, method: MethodCfg,
         hero_name: str = "Mina", hero_type: str = "girl", poppa_type: str = "grandfather") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    poppa = world.add(Entity(id="Poppa", kind="character", type=poppa_type, role="poppa", label="the poppa"))
    sharer = world.add(
        Entity(
            id=sharer_cfg.label,
            kind="character",
            type=sharer_cfg.type,
            role="sharer",
            attrs={"relation": sharer_cfg.relation},
        )
    )
    receiver = world.add(
        Entity(
            id=sharer_cfg.needy_friend,
            kind="character",
            type="child",
            role="receiver",
        )
    )
    shop = world.add(Entity(id="shop", type="shop", label="the shop"))
    item_ent = world.add(Entity(id="item", type="food", label=item.label))
    tag = world.add(Entity(id="tag", type="tag", label="discount card"))

    world.facts.update(
        hero=hero,
        poppa=poppa,
        sharer=sharer,
        receiver=receiver,
        item_cfg=item,
        method_cfg=method,
        sharer_cfg=sharer_cfg,
    )

    receiver.meters["need"] = 0.0
    item_ent.meters["discounted"] = 0.0
    item_ent.meters["shared"] = 0.0
    tag.meters["moved"] = 0.0
    shop.meters["mystery"] = 0.0
    shop.meters["share_basket"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] = 0.0
    sharer.memes["guilt"] = 0.0
    sharer.memes["worry"] = 0.0
    sharer.memes["relief"] = 0.0
    receiver.memes["relief"] = 0.0
    receiver.memes["hope"] = 0.0

    introduce(world, hero, poppa)
    show_item(world, hero, item)

    world.para()
    first_vanish(world, item)
    worry(world, hero, poppa)
    clue(world, item)
    suspect(world, hero, method)

    world.para()
    wait_and_watch(world, hero, poppa)
    move_tag(world, method)
    if sharer_cfg.confesses_early:
        reveal_confession(world, sharer, receiver, item)
    else:
        reveal_caught(world, hero, poppa, sharer, receiver, item, method)
    gentle_talk(world, poppa, sharer, method)

    world.para()
    kind_fix(world, hero, poppa, sharer, receiver, item)

    world.facts.update(
        outcome=outcome_of(
            StoryParams(
                item=item.id,
                sharer=sharer_cfg.id,
                method=method.id,
                hero_name=hero_name,
                hero_type=hero_type,
                poppa_type=poppa_type,
                seed=None,
            )
        ),
        clue=item.clue_trace,
        shared=item_ent.meters["shared"] >= THRESHOLD,
        mystery=shop.meters["mystery"] >= THRESHOLD,
    )
    return world


ITEMS = {
    "loaf": ItemCfg(
        id="loaf",
        label="loaf",
        phrase="a warm round loaf",
        clue="three soft crumbs on the counter",
        clue_trace="crumbs",
        share_text="a loaf could be cut into thick pieces and shared by two children",
        servings=4,
        can_discount=True,
        can_share=True,
        tags={"bread", "sharing", "discount"},
    ),
    "soup": ItemCfg(
        id="soup",
        label="soup pot",
        phrase="a little pot of carrot soup",
        clue="a tiny curl of steam on the glass lid",
        clue_trace="steam",
        share_text="the soup could be poured into two bowls and shared quietly",
        servings=3,
        can_discount=True,
        can_share=True,
        tags={"soup", "sharing", "discount"},
    ),
    "oranges": ItemCfg(
        id="oranges",
        label="bag of oranges",
        phrase="a paper bag of sweet oranges",
        clue="one bright peel thread near the till",
        clue_trace="peel",
        share_text="a bag of oranges could be split hand to hand",
        servings=5,
        can_discount=True,
        can_share=True,
        tags={"orange", "sharing", "discount"},
    ),
    "cupcake": ItemCfg(
        id="cupcake",
        label="cupcake",
        phrase="a single swirled cupcake",
        clue="a dot of icing on the tray",
        clue_trace="icing",
        share_text="it was really only enough for one hungry mouth",
        servings=1,
        can_discount=True,
        can_share=False,
        tags={"cake", "discount"},
    ),
    "teapot": ItemCfg(
        id="teapot",
        label="teapot",
        phrase="a blue painted teapot",
        clue="a little ring where the base had stood",
        clue_trace="ring",
        share_text="it was not food at all",
        servings=0,
        can_discount=False,
        can_share=False,
        tags={"shop"},
    ),
}

SHARERS = {
    "neighbor_boy": SharerCfg(
        id="neighbor_boy",
        label="Tavi",
        type="boy",
        phrase="the baker's neighbor boy",
        reason="he wanted to help someone",
        needy_friend="Oren",
        relation="neighbor",
        bold=3,
        confesses_early=False,
        tags={"child", "sharing"},
    ),
    "older_sister": SharerCfg(
        id="older_sister",
        label="Lina",
        type="girl",
        phrase="hero's older sister",
        reason="she wanted to help someone",
        needy_friend="Pip",
        relation="sibling",
        bold=2,
        confesses_early=True,
        tags={"sibling", "sharing"},
    ),
    "apprentice": SharerCfg(
        id="apprentice",
        label="Nico",
        type="boy",
        phrase="poppa's shy helper",
        reason="he wanted to help someone",
        needy_friend="Mara",
        relation="helper",
        bold=1,
        confesses_early=False,
        tags={"helper", "sharing"},
    ),
}

METHODS = {
    "tiptoe": MethodCfg(
        id="tiptoe",
        label="tiptoeing",
        sense=3,
        boldness=1,
        text="tiptoeing past the biscuit tins",
        tags={"quiet"},
    ),
    "coat_swoop": MethodCfg(
        id="coat_swoop",
        label="a coat swoop",
        sense=2,
        boldness=3,
        text="swooping the long coat hem around the shelf to hide busy hands",
        tags={"reckless"},
    ),
    "window_reach": MethodCfg(
        id="window_reach",
        label="a window reach",
        sense=2,
        boldness=2,
        text="reaching in through the half-open window after closing time",
        tags={"reckless"},
    ),
    "catapult": MethodCfg(
        id="catapult",
        label="a catapult trick",
        sense=1,
        boldness=4,
        text="flicking the card across the room like a toy",
        tags={"nonsense"},
    ),
}


KNOWLEDGE = {
    "discount": [
        (
            "What is a discount?",
            "A discount means something costs less than usual. Shops use discounts when they want to sell something sooner or make it easier for people to buy."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting another person have part of what you have. It can make a hard day lighter because more than one person is cared for."
        )
    ],
    "bread": [
        (
            "Why is a loaf easy to share?",
            "A loaf can be sliced into several pieces. That makes it simple for two or more people to eat from the same food."
        )
    ],
    "soup": [
        (
            "Why is soup easy to share?",
            "Soup can be poured into more than one bowl. Warm food that can be split is often easy to share."
        )
    ],
    "orange": [
        (
            "Why can oranges be shared?",
            "A bag of oranges has more than one piece of fruit. Different people can each take one."
        )
    ],
    "reckless": [
        (
            "What does reckless mean?",
            "Reckless means doing something risky without stopping to think enough first. A reckless choice can come from a kind feeling, but it can still cause trouble."
        )
    ],
}
KNOWLEDGE_ORDER = ["discount", "sharing", "bread", "soup", "orange", "reckless"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    sharer = f["sharer"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old that includes the words "poppa", "discount", and "reckless".',
        f"Tell a small shop mystery where {hero.id} helps poppa, the same clue appears night after night, and the twist is that {sharer.id} was trying to share {item.label} with someone hungry.",
        f"Write a story with repetition, a twist, and sharing: a child fears a thief, then learns that the secret behind the missing discount card came from a kind but reckless plan.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    poppa = f["poppa"]
    sharer = f["sharer"]
    receiver = f["receiver"]
    item = f["item_cfg"]
    method = f["method_cfg"]
    out = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {hero.pronoun('possessive')} poppa, and {sharer.id} in the little shop. They all become part of the mystery around the missing discount card."
        ),
        (
            "What kept happening again and again?",
            f"The discount card kept vanishing night after night. The same kind of clue appeared each time, so the repetition made the mystery feel real and puzzling."
        ),
        (
            "Why did the mystery seem scary at first?",
            f"{hero.id} thought a thief might be sneaking into the shop. {hero.pronoun().capitalize()} imagined a reckless stranger touching things in the dark, which made the quiet shop feel spooky."
        ),
        (
            "What was the twist?",
            f"The person moving the discount card was not trying to steal {item.label}. {sharer.id} was trying to help {receiver.id}, because {item.share_text}."
        ),
        (
            f"Why did poppa still call it reckless?",
            f"Poppa knew the wish to help was kind, but moving the card without asking was reckless. It mixed up the prices and bent trust, even though the reason came from caring."
        ),
    ]
    if out == "confession":
        qa.append(
            (
                f"How was the mystery solved?",
                f"{sharer.id} confessed before anyone had to accuse {sharer.pronoun('object')}. That changed the mood at once, because the secret turned into an honest talk instead of a chase."
            )
        )
    else:
        qa.append(
            (
                "How was the mystery solved?",
                f"{hero.id} and poppa hid and watched until they saw what was happening. When the truth came out, they learned the moving card was part of {sharer.id}'s plan to help {receiver.id}, not to steal."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with a sharing basket instead of a secret trick. From then on, poppa made room for honest help, and the shop felt warm instead of mysterious."
        )
    )
    qa.append(
        (
            f"What did {hero.id} learn?",
            f"{hero.id} learned that a strange clue does not always mean a bad heart. {hero.pronoun().capitalize()} also learned that kindness works best when people tell the truth and share openly."
        )
    )
    _ = method
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"discount", "sharing"}
    item = world.facts["item_cfg"]
    method = world.facts["method_cfg"]
    tags |= set(item.tags)
    if "reckless" in method.tags:
        tags.add("reckless")
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
        bits: list[str] = []
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
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
shareable(I) :- servings(I,S), S >= 2, can_share(I).
valid(I,M)   :- item(I), method(M), can_discount(I), shareable(I), sense(M,S), sense_min(T), S >= T.

outcome(confession)     :- chosen_sharer(S), confesses_early(S).
outcome(caught_in_act)  :- not outcome(confession), chosen_sharer(S), bold(S,B1), chosen_method(M), boldness(M,B2), B1 >= 3, B2 >= 3.
outcome(kind_discovery) :- not outcome(confession), not outcome(caught_in_act).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.can_discount:
            lines.append(asp.fact("can_discount", item_id))
        if item.can_share:
            lines.append(asp.fact("can_share", item_id))
        lines.append(asp.fact("servings", item_id, item.servings))
    for sharer_id, sharer in SHARERS.items():
        lines.append(asp.fact("sharer", sharer_id))
        lines.append(asp.fact("bold", sharer_id, sharer.bold))
        if sharer.confesses_early:
            lines.append(asp.fact("confesses_early", sharer_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("boldness", method_id, method.boldness))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_sharer", params.sharer),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        item="loaf",
        sharer="neighbor_boy",
        method="coat_swoop",
        hero_name="Mina",
        hero_type="girl",
        poppa_type="grandfather",
        seed=None,
    ),
    StoryParams(
        item="soup",
        sharer="older_sister",
        method="tiptoe",
        hero_name="Rafi",
        hero_type="boy",
        poppa_type="grandfather",
        seed=None,
    ),
    StoryParams(
        item="oranges",
        sharer="apprentice",
        method="window_reach",
        hero_name="Lina",
        hero_type="girl",
        poppa_type="grandfather",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a little shop mystery with poppa, a discount card, repetition, a twist, and sharing."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--sharer", choices=SHARERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--poppa-type", choices=["grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible item/method pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Mina", "Tara", "Lulu", "Nora", "Zia", "Pia"]
BOY_NAMES = ["Rafi", "Niko", "Omi", "Tavi", "Eli", "Milo"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item:
        item = ITEMS[args.item]
        if not item.can_discount or not item.shareable:
            raise StoryError(explain_item_rejection(item))
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            raise StoryError(explain_method_rejection(method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.method is None or combo[1] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, method_id = rng.choice(combos)
    sharer_id = args.sharer or rng.choice(sorted(SHARERS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    poppa_type = args.poppa_type or "grandfather"

    return StoryParams(
        item=item_id,
        sharer=sharer_id,
        method=method_id,
        hero_name=hero_name,
        hero_type=hero_type,
        poppa_type=poppa_type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.sharer not in SHARERS:
        raise StoryError(f"(Unknown sharer: {params.sharer})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    item = ITEMS[params.item]
    sharer = SHARERS[params.sharer]
    method = METHODS[params.method]
    if not valid_combo(item, method):
        if not item.can_discount or not item.shareable:
            raise StoryError(explain_item_rejection(item))
        raise StoryError(explain_method_rejection(method))

    world = tell(
        item=item,
        sharer_cfg=sharer,
        method=method,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        poppa_type=params.poppa_type,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases: list[StoryParams] = list(CURATED)
    for s in range(30):
        try:
            ns = build_parser().parse_args([])
            params = resolve_params(ns, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Failed to resolve params for seed {s}.")
            break

    mismatch = 0
    for case in cases:
        ao = asp_outcome(case)
        po = outcome_of(case)
        if ao != po:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, method) pairs:\n")
        for item, method in combos:
            print(f"  {item:10} {method}")
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
            header = f"### {p.hero_name}: {p.item} / {p.sharer} / {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
