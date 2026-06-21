#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/exhibit_parson_dialogue_bravery_humor_space_adventure.py
===================================================================================

A standalone story world about two children turning a church-hall space exhibit
into a grand mission. One child wants to climb the exhibit to reach a stuck
prop, a friend warns them with dialogue and a joke, and a kindly parson shows
what brave, sensible help looks like.

The domain aims for a TinyStories-style "space adventure" tone while staying
grounded in ordinary physical state:

- typed entities with physical meters and emotional memes
- a short causal rule engine
- explicit reasonableness constraints over what can get stuck where
- a Python gate plus an inline ASP twin
- state-driven prose with beginning, turn, and ending image

Run it
------
python storyworlds/worlds/gpt-5.4/exhibit_parson_dialogue_bravery_humor_space_adventure.py
python storyworlds/worlds/gpt-5.4/exhibit_parson_dialogue_bravery_humor_space_adventure.py --all
python storyworlds/worlds/gpt-5.4/exhibit_parson_dialogue_bravery_humor_space_adventure.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/exhibit_parson_dialogue_bravery_humor_space_adventure.py --asp
python storyworlds/worlds/gpt-5.4/exhibit_parson_dialogue_bravery_humor_space_adventure.py --verify
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
SENSE_MIN = 2
BRAVERY_INIT = 5.0
WITTY_TRAITS = {"funny", "quick", "playful", "cheerful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "parson"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return "parson" if self.type == "parson" else self.label or self.type
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
class Exhibit:
    id: str
    label: str
    scene: str
    prop_sentence: str
    mission: str
    snag_points: set[str] = field(default_factory=set)
    wobble_text: str = ""
    ending: str = ""
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
class Item:
    id: str
    label: str
    phrase: str
    snag: str
    height: int
    stuck_text: str
    cheer_text: str
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
    sense: int
    reach: int
    text: str
    fail: str
    qa_text: str
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


def _r_wobble(world: World) -> list[str]:
    exhibit = world.get("exhibit")
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.meters["climbing"] < THRESHOLD or not exhibit.fragile:
        return []
    sig = ("wobble", exhibit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    exhibit.meters["wobble"] += 1
    hero.memes["fear"] += 1
    friend.memes["fear"] += 1
    return ["__wobble__"]


def _r_damage(world: World) -> list[str]:
    exhibit = world.get("exhibit")
    if exhibit.meters["wobble"] < THRESHOLD:
        return []
    delay = int(world.facts.get("delay", 0))
    if delay <= 0:
        return []
    sig = ("damage", exhibit.id, delay)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    exhibit.meters["damage"] += float(delay)
    return ["__damage__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="damage", tag="physical", apply=_r_damage),
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


def item_fits(exhibit: Exhibit, item: Item) -> bool:
    return item.snag in exhibit.snag_points


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def can_reach(response: Response, item: Item) -> bool:
    return response.reach >= item.height


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_responses():
        return combos
    best = max(r.reach for r in sensible_responses())
    for exhibit_id, exhibit in EXHIBITS.items():
        for item_id, item in ITEMS.items():
            if item_fits(exhibit, item) and best >= item.height:
                combos.append((exhibit_id, item_id))
    return combos


def helper_humor(trait: str) -> float:
    return 5.0 if trait in WITTY_TRAITS else 3.0


def would_wait(relation: str, hero_age: int, friend_age: int, trait: str) -> bool:
    older_friend = relation == "siblings" and friend_age > hero_age
    authority = helper_humor(trait) + (3.0 if older_friend else 0.0) + 1.0
    return older_friend and authority > BRAVERY_INIT


def outcome_of(params: "StoryParams") -> str:
    if would_wait(
        relation=params.relation,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
        trait=params.friend_trait,
    ):
        return "waited"
    response = RESPONSES[params.response]
    item = ITEMS[params.item]
    if can_reach(response, item):
        return "rescued"
    return "torn"


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["climbing"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("exhibit").meters["wobble"] >= THRESHOLD,
        "damage": sim.get("exhibit").meters["damage"],
    }


def open_scene(world: World, hero: Entity, friend: Entity, exhibit_cfg: Exhibit) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After lunch, {hero.id} and {friend.id} hurried into the church hall, where "
        f"the space exhibit glowed under strings of tiny silver stars."
    )
    world.say(
        f"{exhibit_cfg.scene} {exhibit_cfg.prop_sentence} Soon the two friends were "
        f"not just in a hall anymore. They were on {exhibit_cfg.mission}."
    )


def discover_problem(world: World, hero: Entity, friend: Entity, item: Item) -> None:
    world.say(
        f"Then {friend.id} pointed up. {item.stuck_text} Without it, the mission did not look ready at all."
    )
    world.say(
        f'"Oh no," said {hero.id}. "We need {item.phrase} back."'
    )


def tempt(world: World, hero: Entity, exhibit_cfg: Exhibit) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} tipped {hero.pronoun("possessive")} chin up. "I can climb the {exhibit_cfg.label} and get it," '
        f'{hero.pronoun()} said.'
    )


def warn(world: World, friend: Entity, hero: Entity, exhibit_cfg: Exhibit) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    friend.memes["humor"] += 1
    friend.memes["caution"] += 1
    joke = ' "If the moon bonks you back, that is not a very grand landing,"'
    extra = ""
    if pred["wobble"]:
        extra = f" The {exhibit_cfg.label} looked lovely, but it did not look strong."
    world.say(
        f'{friend.id} grabbed {hero.id}\'s sleeve.{joke} {friend.pronoun()} whispered. '
        f'"It will wobble if you climb it. Let\'s call the parson instead."{extra}'
    )


def back_down(world: World, hero: Entity, friend: Entity, parson: Entity, response: Response, item: Item) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f'{hero.id} looked up once more, then let out a puff of air. "All right," {hero.pronoun()} said. '
        f'"Brave does not have to mean wobbly."'
    )
    world.say(
        f"The parson heard them from the next table and came over at once. With a warm smile, "
        f"he {response.text.replace('{item}', item.label)}."
    )


def climb(world: World, hero: Entity, exhibit_cfg: Exhibit) -> None:
    hero.meters["climbing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before anyone could stop {hero.pronoun('object')}, {hero.id} put one sneaker on the edge of the "
        f"{exhibit_cfg.label} and reached upward."
    )
    if world.get("exhibit").meters["wobble"] >= THRESHOLD:
        world.say(exhibit_cfg.wobble_text)
    if world.get("exhibit").meters["damage"] >= THRESHOLD:
        world.say(
            "A paper planet ring tore loose and spun down in a sleepy, glittery twirl."
        )


def call_for_help(world: World, friend: Entity) -> None:
    world.say(f'"Parson!" {friend.id} called. "Please help us before our spaceship becomes confetti!"')


def rescue(world: World, parson: Entity, response: Response, item: Item) -> None:
    exhibit = world.get("exhibit")
    item_ent = world.get("item")
    item_ent.meters["stuck"] = 0.0
    item_ent.meters["reached"] += 1
    exhibit.meters["wobble"] = 0.0
    world.say(
        f"The parson came quickly, black coat swishing like a captain's cape. "
        f'"No one blast off with their feet," he said, and his eyes twinkled. '
        f"Then he {response.text.replace('{item}', item.label)}."
    )


def rescue_fail(world: World, parson: Entity, response: Response, item: Item) -> None:
    exhibit = world.get("exhibit")
    exhibit.meters["closed"] += 1
    world.say(
        f"The parson hurried over and {response.fail.replace('{item}', item.label)}. "
        f"The {exhibit.label} gave another unhappy wobble."
    )
    world.say(
        "At last he lifted the child down first, because people mattered more than props."
    )


def lesson(world: World, parson: Entity, hero: Entity, friend: Entity) -> None:
    hero.memes["lesson"] += 1
    friend.memes["joy"] += 1
    hero.memes["fear"] = 0.0
    friend.memes["fear"] = 0.0
    world.say(
        f'The parson knelt beside them. "That was a good call for help," he said softly. '
        f'"Real bravery is not showing off. Real bravery is choosing the safe thing when the exciting thing is silly."'
    )
    world.say(
        f'{friend.id} gave a tiny grin. "{friend.pronoun("subject").capitalize()} did say the moon might bonk back," '
        f'said {hero.id}.'
    )


def repair_and_end(world: World, hero: Entity, friend: Entity, exhibit_cfg: Exhibit, item: Item, outcome: str) -> None:
    exhibit = world.get("exhibit")
    if outcome == "torn":
        hero.memes["sadness"] += 1
        friend.memes["sadness"] += 1
        world.say(
            "The mission had to close for a little while so the torn ring could be taped back in place."
        )
        world.say(
            f"Later, when the stars were smooth again, {hero.id} and {friend.id} stood on the floor and saluted the repaired ship. "
            f"They still played their game, only this time they kept both boots planted safely below."
        )
        return
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Once {item.phrase} was back in their hands, the mission felt whole again. {item.cheer_text}"
    )
    world.say(
        f"{exhibit_cfg.ending} Even the parson gave them a solemn space salute, which made them laugh so hard they nearly forgot the scare."
    )


def tell(
    exhibit_cfg: Exhibit,
    item: Item,
    response: Response,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    friend_trait: str = "funny",
    relation: str = "friends",
    hero_age: int = 5,
    friend_age: int = 6,
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=["bold"],
            age=hero_age,
            attrs={"relation": relation},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=[friend_trait],
            age=friend_age,
            attrs={"relation": relation},
        )
    )
    parson = world.add(
        Entity(
            id="Parson",
            kind="character",
            type="parson",
            role="adult",
            label="the parson",
            traits=["calm", "kind"],
        )
    )
    exhibit = world.add(
        Entity(
            id="exhibit",
            kind="thing",
            type="exhibit",
            label=exhibit_cfg.label,
            fragile=True,
        )
    )
    item_ent = world.add(
        Entity(
            id="item",
            kind="thing",
            type="prop",
            label=item.label,
        )
    )
    item_ent.meters["stuck"] = 1.0
    world.facts["delay"] = delay

    hero.memes["bravery"] = BRAVERY_INIT
    friend.memes["humor"] = helper_humor(friend_trait)

    open_scene(world, hero, friend, exhibit_cfg)
    discover_problem(world, hero, friend, item)

    world.para()
    tempt(world, hero, exhibit_cfg)
    warn(world, friend, hero, exhibit_cfg)

    waited = would_wait(
        relation=relation,
        hero_age=hero_age,
        friend_age=friend_age,
        trait=friend_trait,
    )
    if waited:
        back_down(world, hero, friend, parson, response, item)
        outcome = "waited"
        world.para()
        lesson(world, parson, hero, friend)
        world.para()
        repair_and_end(world, hero, friend, exhibit_cfg, item, outcome)
    else:
        world.para()
        climb(world, hero, exhibit_cfg)
        call_for_help(world, friend)

        world.para()
        if can_reach(response, item):
            rescue(world, parson, response, item)
            outcome = "rescued"
            world.para()
            lesson(world, parson, hero, friend)
            world.para()
            repair_and_end(world, hero, friend, exhibit_cfg, item, outcome)
        else:
            rescue_fail(world, parson, response, item)
            outcome = "torn"
            world.para()
            lesson(world, parson, hero, friend)
            world.para()
            repair_and_end(world, hero, friend, exhibit_cfg, item, outcome)

    world.facts.update(
        hero=hero,
        friend=friend,
        parson=parson,
        exhibit_cfg=exhibit_cfg,
        exhibit=exhibit,
        item_cfg=item,
        item=item_ent,
        response=response,
        relation=relation,
        outcome=outcome,
        reached=item_ent.meters["reached"] >= THRESHOLD,
        waited=waited,
    )
    return world


EXHIBITS = {
    "rocket": Exhibit(
        id="rocket",
        label="cardboard rocket",
        scene="A silver cardboard rocket stood in the middle, and a painted moon hung behind it.",
        prop_sentence="A string of foil stars trembled over the nose cone.",
        mission="the last bright mile before Mars",
        snag_points={"fin", "nose"},
        wobble_text="The cardboard rocket gave a thin creak and swayed from side to side.",
        ending="Soon they were back on their journey, counting stars and whispering into pretend radios.",
        tags={"rocket", "space"},
    ),
    "moonbuggy": Exhibit(
        id="moonbuggy",
        label="moon buggy",
        scene="A moon buggy made from painted boxes waited under a purple paper sky.",
        prop_sentence="Its dish antenna leaned over a trail of glittering rocks.",
        mission="the dusty hills of the moon",
        snag_points={"dish", "handle"},
        wobble_text="The moon buggy rattled on its box wheels, and the dish antenna bobbed like a worried ear.",
        ending="After that, they drove the moon buggy only with imagination, which was more than enough fuel.",
        tags={"moon", "space"},
    ),
    "aliengate": Exhibit(
        id="aliengate",
        label="alien gate",
        scene="A tall alien gate arched over green paper stones and a sign that said WELCOME, EXPLORERS.",
        prop_sentence="Soft lamps made its painted swirls shine as if they knew a secret.",
        mission="a strange, friendly world beyond Saturn",
        snag_points={"arch", "hook"},
        wobble_text="The alien gate shivered, and one green paper stone skidded a little across the floor.",
        ending="Before long they were tiptoeing through the alien gate again, brave and careful together.",
        tags={"alien", "space"},
    ),
}

ITEMS = {
    "badge": Item(
        id="badge",
        label="captain badge",
        phrase="the captain badge",
        snag="fin",
        height=1,
        stuck_text="The captain badge had slipped up onto a shiny fin of the display.",
        cheer_text="Mia pinned it on and stood taller at once, while the other child announced a most important countdown.",
        tags={"badge", "bravery"},
    ),
    "map": Item(
        id="map",
        label="star map",
        phrase="the star map",
        snag="dish",
        height=2,
        stuck_text="The folded star map had landed across the buggy's dish antenna like a sleepy bird.",
        cheer_text="They spread the map wide and argued happily about which crater looked most like a pancake.",
        tags={"map", "space"},
    ),
    "banana": Item(
        id="banana",
        label="rubber banana",
        phrase="the rubber banana",
        snag="hook",
        height=3,
        stuck_text="Someone's rubber banana had hooked itself on the highest point of the gate, which made the whole brave mission look wonderfully silly.",
        cheer_text="They decided every proper space crew must carry one emergency banana for laughing at hard moments.",
        tags={"banana", "humor"},
    ),
}

RESPONSES = {
    "stool": Response(
        id="stool",
        sense=3,
        reach=2,
        text="brought over a little step stool, steadied it with one hand, and lifted down the {item}",
        fail="fetched a little step stool, but even standing safely on it he still could not reach the {item}",
        qa_text="used a step stool and lifted the item down",
        tags={"stool", "help"},
    ),
    "reacher": Response(
        id="reacher",
        sense=3,
        reach=3,
        text="fetched the long litter-picker from the tidy cupboard and hooked the {item} down in one neat try",
        fail="tried with a litter-picker, but the {item} was twisted too tightly to come free that way",
        qa_text="used a long reacher to hook the item down",
        tags={"reacher", "help"},
    ),
    "ladder": Response(
        id="ladder",
        sense=2,
        reach=3,
        text="opened the little library ladder, held it firm, and took down the {item}",
        fail="opened the little ladder, but the {item} had snagged too awkwardly to come free at once",
        qa_text="used a ladder and took the item down safely",
        tags={"ladder", "help"},
    ),
    "jump": Response(
        id="jump",
        sense=1,
        reach=1,
        text="jumped for the {item} and somehow caught it",
        fail="jumped for the {item}, but only made the display wobble more",
        qa_text="jumped for the item",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Ella", "Nora", "Ruby", "Lucy"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Eli", "Finn", "Theo"]
TRAITS = ["funny", "quick", "careful", "playful", "cheerful", "steady"]


@dataclass
class StoryParams:
    exhibit: str
    item: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    friend_trait: str
    relation: str
    hero_age: int = 5
    friend_age: int = 6
    delay: int = 0
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


KNOWLEDGE = {
    "rocket": [
        (
            "What is a rocket?",
            "A rocket is a vehicle that can travel into space by pushing hot gas down so it shoots up. Real rockets are strong, but cardboard play rockets are only for pretending.",
        )
    ],
    "moon": [
        (
            "What is the moon?",
            "The moon is the big round world that goes around Earth. It shines because sunlight bounces off it.",
        )
    ],
    "alien": [
        (
            "What does alien mean in a space story?",
            "In a space story, an alien is a creature from another world. In pretend play, aliens can be funny or friendly instead of scary.",
        )
    ],
    "map": [
        (
            "What is a star map?",
            "A star map is a picture that helps you find stars or places in the sky. In pretend space play, it can help explorers decide where to go next.",
        )
    ],
    "banana": [
        (
            "Why can a joke help when you feel scared?",
            "A gentle joke can make your body loosen a little and help you think clearly again. Laughing does not fix danger by itself, but it can help you stay calm enough to choose a safe plan.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel excited or worried. Sometimes the brave choice is asking for help instead of doing something risky.",
        )
    ],
    "help": [
        (
            "Why is it smart to ask a grown-up for help with something high up?",
            "A grown-up can use the right tool and keep the area steady. That makes it less likely that someone will fall or break something.",
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool is a small sturdy platform that helps a person reach something a little higher. It should be used carefully on the floor, not on top of shaky things.",
        )
    ],
    "reacher": [
        (
            "What is a reacher tool?",
            "A reacher is a long tool that helps you grab something without climbing. It is useful when the safe floor is a better place to stay.",
        )
    ],
    "ladder": [
        (
            "Why do ladders need someone to hold them steady?",
            "A ladder can tip or slide if it is not set up carefully. Having it placed properly and held steady helps keep people safe.",
        )
    ],
    "parson": [
        (
            "What is a parson?",
            "A parson is a church minister. In some stories, a parson is the kindly grown-up who helps people and keeps calm when something goes wrong.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "parson",
    "rocket",
    "moon",
    "alien",
    "map",
    "banana",
    "bravery",
    "help",
    "stool",
    "reacher",
    "ladder",
]


def pair_noun(hero: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and friend.type == "boy":
            return "two brothers"
        if hero.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    exhibit_cfg = f["exhibit_cfg"]
    item = f["item_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short space adventure for a 3-to-5-year-old that includes the words '
        f'"exhibit" and "parson", uses dialogue, bravery, and humor, and centers on a child '
        f'at a church-hall space exhibit.'
    )
    if outcome == "waited":
        return [
            base,
            f"Tell a gentle story where {hero.id} wants to climb a {exhibit_cfg.label} to get {item.phrase}, "
            f"but {friend.id} makes a joke, warns about the wobble, and the parson helps safely.",
            f'Write a story where the bravest choice turns out to be waiting for help, and end with the children laughing and returning to their pretend mission.',
        ]
    if outcome == "rescued":
        return [
            base,
            f"Tell a story where {hero.id} tries to climb after {item.phrase}, the exhibit wobbles, "
            f"and the parson fixes the problem with the right tool.",
            f'Write a funny, child-friendly rescue scene where a calm parson in a church hall teaches that brave does not mean reckless.',
        ]
    return [
        base,
        f"Tell a cautionary story where {hero.id} climbs the exhibit, the display tears, and the parson helps everyone calm down before the game can continue.",
        f'Write a story with a small sad turn, but keep it gentle and safe: nobody is hurt, yet the children learn to keep their feet on the floor and ask for help next time.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parson = f["parson"]
    exhibit_cfg = f["exhibit_cfg"]
    item = f["item_cfg"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(hero, friend, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {friend.id}, at a space exhibit, and a helpful parson who comes to help them.",
        ),
        (
            "What problem did the children find at the exhibit?",
            f"They saw that {item.phrase} was stuck high on the {exhibit_cfg.label}. Without it, their pretend mission felt unfinished.",
        ),
        (
            f"Why did {friend.id} tell {hero.id} not to climb?",
            f"{friend.id} could see the {exhibit_cfg.label} was shaky and guessed it would wobble if someone climbed it. {friend.pronoun('subject').capitalize()} even used a joke to make the warning easier to hear.",
        ),
    ]
    if f["outcome"] == "waited":
        qa.append(
            (
                f"What brave choice did {hero.id} make?",
                f"{hero.id} chose not to climb after all and waited for help instead. That was brave because {hero.pronoun('subject')} gave up the exciting choice in order to make the safe one.",
            )
        )
        qa.append(
            (
                "How did the parson solve the problem?",
                f"The parson {response.qa_text}. He could help because he used a sensible tool while everyone stayed safely on the floor.",
            )
        )
    elif f["outcome"] == "rescued":
        qa.append(
            (
                f"What happened when {hero.id} climbed the exhibit?",
                f"The {exhibit_cfg.label} wobbled and scared both children. The danger came from treating a fragile display like a ladder.",
            )
        )
        qa.append(
            (
                "How did the parson help?",
                f"The parson {response.qa_text}. His calm help stopped the wobble and turned the scary moment into a lesson.",
            )
        )
    else:
        qa.append(
            (
                f"What went wrong before the parson fixed things?",
                f"When {hero.id} climbed, the display wobbled so much that part of it tore loose. Nobody was hurt, but the game had to pause because the exhibit needed repair.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended gently: the children waited while the exhibit was fixed, and later they played again with both feet on the floor. The ending shows they had changed what bravery meant.",
            )
        )
    qa.append(
        (
            "What lesson did the children learn?",
            f"They learned that bravery is not the same as showing off. In this story, the brave thing was asking for help and keeping the exhibit safe for everyone.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"parson", "bravery", "help"}
    exhibit_id = f["exhibit_cfg"].id
    item_id = f["item_cfg"].id
    response_id = f["response"].id
    if exhibit_id == "rocket":
        tags.add("rocket")
    elif exhibit_id == "moonbuggy":
        tags.add("moon")
    elif exhibit_id == "aliengate":
        tags.add("alien")
    if item_id == "map":
        tags.add("map")
    if item_id == "banana":
        tags.add("banana")
    if response_id in {"stool", "reacher", "ladder"}:
        tags.add(response_id)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.fragile:
            bits.append("fragile=True")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
fits(E, I) :- exhibit(E), item(I), snag_point(E, P), needs(I, P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
reachable(I) :- item(I), item_height(I, H), best_reach(B), H <= B.
valid(E, I) :- fits(E, I), reachable(I).

best_reach(R) :- R = #max { K : sensible(SR), reach(SR, K) }.

% --- outcome model ---------------------------------------------------------
witty_now(T) :- trait(T), witty(T).
humor_score(5) :- witty_now(T).
humor_score(3) :- trait(T), not witty_now(T).
older_friend :- relation(siblings), friend_age(FA), hero_age(HA), FA > HA.
authority(H + 1 + B) :- humor_score(H), older_friend, B = 3.
authority(H + 1) :- humor_score(H), not older_friend.
waited :- older_friend, authority(A), bravery_init(BR), A > BR.

rescued :- not waited, chosen_response(R), chosen_item(I), reach(R, RR), item_height(I, H), RR >= H.
outcome(waited) :- waited.
outcome(rescued) :- not waited, rescued.
outcome(torn) :- not waited, not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for exhibit_id, exhibit in EXHIBITS.items():
        lines.append(asp.fact("exhibit", exhibit_id))
        for point in sorted(exhibit.snag_points):
            lines.append(asp.fact("snag_point", exhibit_id, point))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("needs", item_id, item.snag))
        lines.append(asp.fact("item_height", item_id, item.height))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("reach", response_id, response.reach))
    for trait in sorted(WITTY_TRAITS):
        lines.append(asp.fact("witty", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_response", params.response),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("friend_age", params.friend_age),
            asp.fact("trait", params.friend_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation/emit succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a space exhibit, a risky climb, a calm parson, and a safer kind of bravery."
    )
    ap.add_argument("--exhibit", choices=EXHIBITS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra wobble damage after the climb")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid exhibit/item set from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def explain_rejection(exhibit: Exhibit, item: Item) -> str:
    return (
        f"(No story: {item.phrase.capitalize()} cannot sensibly get stuck on the {exhibit.label} in this world. "
        f"The item needs a different kind of point to snag on.)"
    )


def explain_response(response_id: str, item_id: str = "") -> str:
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        good = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try one of: {good}.)"
        )
    if item_id and not can_reach(response, ITEMS[item_id]):
        return (
            f"(Refusing response '{response_id}': it cannot reach {ITEMS[item_id].phrase}. "
            f"Choose a taller tool.)"
        )
    return "(No story: response rejected.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.exhibit and args.item:
        exhibit = EXHIBITS[args.exhibit]
        item = ITEMS[args.item]
        if not item_fits(exhibit, item):
            raise StoryError(explain_rejection(exhibit, item))
    if args.response:
        if RESPONSES[args.response].sense < SENSE_MIN:
            raise StoryError(explain_response(args.response))
        if args.item and not can_reach(RESPONSES[args.response], ITEMS[args.item]):
            raise StoryError(explain_response(args.response, args.item))

    combos = [
        combo
        for combo in valid_combos()
        if (args.exhibit is None or combo[0] == args.exhibit)
        and (args.item is None or combo[1] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    exhibit_id, item_id = rng.choice(sorted(combos))
    item = ITEMS[item_id]

    sensible = [r.id for r in sensible_responses() if can_reach(r, item)]
    if args.response is not None:
        if args.response not in sensible:
            raise StoryError(explain_response(args.response, item_id))
        response_id = args.response
    else:
        response_id = rng.choice(sorted(sensible))

    relation = args.relation or rng.choice(["siblings", "friends"])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    friend_trait = rng.choice(TRAITS)
    hero_age, friend_age = rng.sample([4, 5, 6, 7], 2)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)

    return StoryParams(
        exhibit=exhibit_id,
        item=item_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
        relation=relation,
        hero_age=hero_age,
        friend_age=friend_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.exhibit not in EXHIBITS:
        raise StoryError(f"(Unknown exhibit '{params.exhibit}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item '{params.item}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    exhibit = EXHIBITS[params.exhibit]
    item = ITEMS[params.item]
    response = RESPONSES[params.response]

    if not item_fits(exhibit, item):
        raise StoryError(explain_rejection(exhibit, item))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not would_wait(
        relation=params.relation,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
        trait=params.friend_trait,
    ) and not can_reach(response, item):
        raise StoryError(explain_response(params.response, params.item))

    world = tell(
        exhibit_cfg=exhibit,
        item=item,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        friend_trait=params.friend_trait,
        relation=params.relation,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
        delay=params.delay,
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


CURATED = [
    StoryParams(
        exhibit="rocket",
        item="badge",
        response="stool",
        hero_name="Mia",
        hero_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        friend_trait="funny",
        relation="siblings",
        hero_age=5,
        friend_age=7,
        delay=0,
    ),
    StoryParams(
        exhibit="moonbuggy",
        item="map",
        response="stool",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Lily",
        friend_gender="girl",
        friend_trait="careful",
        relation="friends",
        hero_age=6,
        friend_age=5,
        delay=0,
    ),
    StoryParams(
        exhibit="aliengate",
        item="banana",
        response="reacher",
        hero_name="Ava",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        friend_trait="quick",
        relation="friends",
        hero_age=6,
        friend_age=6,
        delay=0,
    ),
    StoryParams(
        exhibit="aliengate",
        item="banana",
        response="ladder",
        hero_name="Sam",
        hero_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        friend_trait="playful",
        relation="siblings",
        hero_age=7,
        friend_age=5,
        delay=1,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (exhibit, item) combos:\n")
        for exhibit_id, item_id in combos:
            print(f"  {exhibit_id:10} {item_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.exhibit} / {p.item} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
