#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flirt_soup_archer_humor_inner_monologue_slice.py
============================================================================

A standalone story world about a small town soup lunch beside an archery lane:
someone tries to flirt with an archer by carrying over a bowl of soup, has a
brief awkward wobble, and finds a gentle, funny way to connect.

The world is slice-of-life, light, and state-driven. The core constraint is
physical common sense: some soups need steadier support than others, and some
approaches make sense only when the archer's hands are actually free enough.
The prose is driven by typed entities with physical meters and emotional memes,
plus a small forward-chaining rule set.

Run it
------
    python storyworlds/worlds/gpt-5.4/flirt_soup_archer_humor_inner_monologue_slice.py
    python storyworlds/worlds/gpt-5.4/flirt_soup_archer_humor_inner_monologue_slice.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/flirt_soup_archer_humor_inner_monologue_slice.py --all --qa
    python storyworlds/worlds/gpt-5.4/flirt_soup_archer_humor_inner_monologue_slice.py --trace
    python storyworlds/worlds/gpt-5.4/flirt_soup_archer_humor_inner_monologue_slice.py --json
    python storyworlds/worlds/gpt-5.4/flirt_soup_archer_humor_inner_monologue_slice.py --asp
    python storyworlds/worlds/gpt-5.4/flirt_soup_archer_humor_inner_monologue_slice.py --verify
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
STEADY_MIN = 2


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
        female = {"girl", "woman", "sister", "server"}
        male = {"boy", "man", "brother", "archer"}
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
class Venue:
    id: str
    place: str
    archery_spot: str
    soup_table: str
    bench: str
    light: str
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


@dataclass
class Soup:
    id: str
    label: str
    phrase: str
    steam: str
    color: str
    slosh: int
    heat: int
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
class ArcherTask:
    id: str
    action: str
    pose: str
    hands_free: int
    focus: int
    patience: int
    can_chat_now: bool
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
class Support:
    id: str
    label: str
    phrase: str
    steady: int
    polite_bonus: int
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
class Approach:
    id: str
    opener: str
    style: str
    boldness: int
    polite: bool
    sets_down: bool
    humor: bool
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
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
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


def support_needed(soup: Soup) -> int:
    return soup.slosh + soup.heat


def support_ok(soup: Soup, support: Support) -> bool:
    return support.steady >= support_needed(soup)


def approach_possible(task: ArcherTask, approach: Approach) -> bool:
    if task.hands_free == 0 and not approach.sets_down:
        return False
    return True


def compatibility_score(task: ArcherTask, approach: Approach, support: Support) -> int:
    return task.patience + support.polite_bonus + (1 if approach.polite else 0) - approach.boldness


def valid_combo(soup: Soup, task: ArcherTask, support: Support, approach: Approach) -> bool:
    return support_ok(soup, support) and approach_possible(task, approach)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for venue_id in VENUES:
        for soup_id, soup in SOUPS.items():
            for task_id, task in TASKS.items():
                for support_id, support in SUPPORTS.items():
                    for approach_id, approach in APPROACHES.items():
                        if valid_combo(soup, task, support, approach):
                            out.append((venue_id, soup_id, task_id, support_id, approach_id))
    return out


def outcome_of(params: "StoryParams") -> str:
    soup = SOUPS[params.soup]
    task = TASKS[params.task]
    support = SUPPORTS[params.support]
    approach = APPROACHES[params.approach]
    if not valid_combo(soup, task, support, approach):
        return "invalid"
    if task.can_chat_now and compatibility_score(task, approach, support) >= 1:
        return "shared_lunch"
    if support.steady >= STEADY_MIN:
        return "saved_face"
    return "awkward_exit"


def _r_focus_interrupt(world: World) -> list[str]:
    hero = world.get("hero")
    archer = world.get("archer")
    if world.facts["task"].focus < 2:
        return []
    if hero.meters["offer_started"] < THRESHOLD:
        return []
    sig = ("focus_interrupt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["wobble"] += 1
    hero.memes["fluster"] += 1
    archer.memes["surprise"] += 1
    return ["__wobble__"]


def _r_support_saves(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["wobble"] < THRESHOLD:
        return []
    if world.facts["support"].steady < STEADY_MIN:
        return []
    sig = ("support_saves",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["spill"] = 0.0
    hero.meters["saved_by_support"] += 1
    hero.memes["hope"] += 1
    return []


def _r_joke_eases(world: World) -> list[str]:
    hero = world.get("hero")
    archer = world.get("archer")
    if not world.facts["approach"].humor:
        return []
    if hero.meters["offer_started"] < THRESHOLD:
        return []
    sig = ("joke_eases",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["ease"] += 1
    archer.memes["ease"] += 1
    archer.memes["amusement"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="focus_interrupt", tag="physical", apply=_r_focus_interrupt),
    Rule(name="support_saves", tag="physical", apply=_r_support_saves),
    Rule(name="joke_eases", tag="social", apply=_r_joke_eases),
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


def predict_offer(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["offer_started"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("hero").meters["wobble"] >= THRESHOLD,
        "saved": sim.get("hero").meters["saved_by_support"] >= THRESHOLD,
        "chat_now": sim.facts["task"].can_chat_now,
    }


def opening_scene(world: World, hero: Entity, archer: Entity, soup: Soup, task: ArcherTask) -> None:
    venue = world.venue
    hero.memes["notice"] += 1
    archer.memes["focus"] += float(task.focus)
    world.say(
        f"At {venue.place}, the lunch table stood only a few steps from {venue.archery_spot}. "
        f"{venue.light} drifted across the floor, and the room smelled like {soup.label}."
    )
    world.say(
        f"{hero.id} was helping ladle {soup.phrase} at {venue.soup_table} when {hero.pronoun()} noticed "
        f"{archer.id}, the local archer, {task.pose}."
    )
    world.say(
        f'In {hero.pronoun("possessive")} head, a tiny voice said, "This is not a flirt. '
        f'This is just soup with feelings."'
    )


def decide(world: World, hero: Entity, soup: Soup, support: Support, approach: Approach) -> None:
    hero.memes["crush"] += 1
    hero.meters["offer_started"] += 1
    world.say(
        f"{hero.id} set one bowl of {soup.color} soup onto {support.phrase} and took a breath."
    )
    world.say(
        f'Another thought arrived at once: "If I walk over there calmly, it will look natural. '
        f'If I trip, I will become a folk tale."'
    )
    world.say(approach.opener)
    propagate(world, narrate=False)


def near_wobble(world: World, hero: Entity, soup: Soup, support: Support, task: ArcherTask) -> None:
    if hero.meters["wobble"] < THRESHOLD:
        return
    world.say(
        f"But {archer_label(world)} was still {task.action}, and for one silly second the bowl tilted."
    )
    if hero.meters["saved_by_support"] >= THRESHOLD:
        world.say(
            f"The {support.label} kept the {soup.label} from leaping over the edge. "
            f"{hero.id} managed not to baptize the archery lane in {soup.label}."
        )


def archer_label(world: World) -> str:
    return world.get("archer").id


def response_scene(world: World, hero: Entity, archer: Entity, task: ArcherTask, approach: Approach) -> None:
    if task.can_chat_now:
        archer.memes["warmth"] += 1
        if approach.humor:
            world.say(
                f"{archer.id} looked up first with surprise, then with a grin. "
                f'"That may be the nicest bowl of soup ever aimed at me," {archer.pronoun()} said.'
            )
        else:
            world.say(
                f"{archer.id} looked up and smiled. "
                f'"Thank you," {archer.pronoun().capitalize()} said, soft enough to make the whole moment feel smaller and warmer.'
            )
    else:
        archer.memes["warmth"] += 1
        world.say(
            f"{archer.id} lowered the bow and stepped back from the line. "
            f'"Give me one second," {archer.pronoun()} said. "{approach.style.capitalize()} was a brave choice."'
        )


def resolve(world: World, hero: Entity, archer: Entity, soup: Soup, approach: Approach, outcome: str) -> None:
    venue = world.venue
    if outcome == "shared_lunch":
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        archer.memes["joy"] += 1
        world.say(
            f"{archer.id} set the bow aside, took the bowl, and nodded toward {venue.bench}. "
            f'Soon they were eating together while the steam from the {soup.label} drew little clouds between them.'
        )
        if approach.humor:
            world.say(
                f'{hero.id} admitted, "I was trying to be smooth." '
                f'{archer.id} laughed. "You were carrying soup to an archer. Smooth was never really the plan."'
            )
        else:
            world.say(
                f'In {hero.pronoun("possessive")} head, the tiny voice changed its mind at last: '
                f'"All right. Maybe this is a flirt. A very careful, soup-based flirt."'
            )
        world.say(
            f"By the time the bowls were empty, the room still felt ordinary in the best way, "
            f"except now {hero.id} knew which soup {archer.id} liked and {archer.id} knew {hero.id}'s laugh."
        )
    elif outcome == "saved_face":
        hero.memes["relief"] += 1
        archer.memes["kindness"] += 1
        world.say(
            f'{archer.id} saw the wobble, rescued the moment by pointing to {venue.bench}, and said, '
            f'"Set it there? I want that soup, and I also want your sleeves to survive."'
        )
        world.say(
            f"{hero.id} obeyed with great dignity, which is to say with very pink cheeks. "
            f"A minute later {archer.id} came over, thanked {hero.pronoun('object')}, and sat beside {hero.pronoun('object')} anyway."
        )
        world.say(
            f"The flirt had not been graceful, but it had become a joke they were both in on, "
            f"which turned out to be almost better."
        )
    else:
        hero.memes["embarrassment"] += 1
        world.say(
            f"{hero.id} set the bowl down too quickly, muttered something that sounded like a weather report, "
            f"and retreated to {world.venue.soup_table}."
        )
        world.say(
            f"Then {archer.id} appeared a little later with the empty bowl and a gentle smile. "
            f'"Next time," {archer.pronoun()} said, "start with hello. Then bring the soup."'
        )
        world.say(
            f"{hero.id} laughed so hard that the embarrassment broke. The next bowl {hero.pronoun()} carried looked steadier already."
        )
def tell(
    soup: Soup,
    task: Task,
    support: Support,
    approach: Approach,
    hero_name: str,
    hero_type: HeroType,
    archer_name: str,
    archer_type: ArcherType,
    friend_name: str,
    friend_type: FriendType,
    venue=None,
) -> World:
    world = World(venue)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    archer = world.add(Entity(id=archer_name, kind="character", type=archer_type, role="archer", label=archer_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", label=friend_name))
    bowl = world.add(Entity(id="bowl", kind="thing", type="bowl", label=soup.label))
    room = world.add(Entity(id="room", kind="thing", type="room", label=venue.place))

    world.facts.update(
        hero=hero,
        archer=archer,
        friend=friend,
        bowl=bowl,
        room=room,
        venue=venue,
        soup=soup,
        task=task,
        support=support,
        approach=approach,
    )

    opening_scene(world, hero, archer, soup, task)

    world.para()
    world.say(
        f'{friend.id} leaned over the ladle and whispered, "If you are going to walk soup over there, at least use {support.phrase}."'
    )
    pred = predict_offer(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_chat_now"] = pred["chat_now"]
    decide(world, hero, soup, support, approach)

    world.para()
    near_wobble(world, hero, soup, support, task)
    response_scene(world, hero, archer, task, approach)

    world.para()
    outcome = outcome_of(
        StoryParams(
            venue=venue.id,
            soup=soup.id,
            task=task.id,
            support=support.id,
            approach=approach.id,
            hero_name=hero_name,
            hero_type=hero_type,
            archer_name=archer_name,
            archer_type=archer_type,
            friend_name=friend_name,
            friend_type=friend_type,
            seed=None,
        )
    )
    resolve(world, hero, archer, soup, approach, outcome)
    world.facts["outcome"] = outcome
    world.facts["shared_lunch"] = outcome in {"shared_lunch", "saved_face"}
    world.facts["wobble_happened"] = hero.meters["wobble"] >= THRESHOLD
    world.facts["support_saved"] = hero.meters["saved_by_support"] >= THRESHOLD
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


VENUES = {
    "hall": Venue(
        id="hall",
        place="the community hall",
        archery_spot="the taped-off practice lane",
        soup_table="the folding lunch table",
        bench="the old window bench",
        light="Late afternoon light",
    ),
    "gym": Venue(
        id="gym",
        place="the school gym",
        archery_spot="the netted archery corner",
        soup_table="the booster-club table",
        bench="the low wooden bench",
        light="Soft gold light",
    ),
    "market": Venue(
        id="market",
        place="the covered town market",
        archery_spot="the straw-target booth",
        soup_table="the stall with the big silver pot",
        bench="the painted bench near the herbs",
        light="Warm market light",
    ),
}

SOUPS = {
    "tomato": Soup(
        id="tomato",
        label="tomato soup",
        phrase="a bowl of tomato soup",
        steam="bright steam",
        color="red",
        slosh=1,
        heat=1,
        tags={"soup", "tomato"},
    ),
    "pumpkin": Soup(
        id="pumpkin",
        label="pumpkin soup",
        phrase="a bowl of pumpkin soup",
        steam="gentle orange steam",
        color="golden",
        slosh=1,
        heat=1,
        tags={"soup", "pumpkin"},
    ),
    "noodle": Soup(
        id="noodle",
        label="noodle soup",
        phrase="a deep bowl of noodle soup",
        steam="noisy noodle steam",
        color="clear",
        slosh=2,
        heat=1,
        tags={"soup", "noodle"},
    ),
}

TASKS = {
    "resting": ArcherTask(
        id="resting",
        action="resting between ends",
        pose="was sitting on the bench with the bow across his knees",
        hands_free=2,
        focus=0,
        patience=2,
        can_chat_now=True,
        tags={"archer", "rest"},
    ),
    "scoring": ArcherTask(
        id="scoring",
        action="writing down scores on a little card",
        pose="was checking the target card with a pencil tucked behind his ear",
        hands_free=1,
        focus=1,
        patience=2,
        can_chat_now=True,
        tags={"archer", "score"},
    ),
    "practicing": ArcherTask(
        id="practicing",
        action="drawing another careful shot",
        pose="was standing very still on the line, bow lifted, one eye narrowed",
        hands_free=0,
        focus=2,
        patience=1,
        can_chat_now=False,
        tags={"archer", "practice"},
    ),
    "packing": ArcherTask(
        id="packing",
        action="sliding arrows back into a canvas tube",
        pose="was kneeling by his bag, packing arrows one by one",
        hands_free=1,
        focus=1,
        patience=1,
        can_chat_now=True,
        tags={"archer", "pack"},
    ),
}

SUPPORTS = {
    "tray": Support(
        id="tray",
        label="tray",
        phrase="a little tray",
        steady=3,
        polite_bonus=1,
        tags={"tray", "steady"},
    ),
    "board": Support(
        id="board",
        label="bread board",
        phrase="a bread board",
        steady=2,
        polite_bonus=0,
        tags={"board", "steady"},
    ),
    "napkin": Support(
        id="napkin",
        label="folded napkin",
        phrase="a folded napkin",
        steady=1,
        polite_bonus=0,
        tags={"napkin"},
    ),
}

APPROACHES = {
    "joke_offer": Approach(
        id="joke_offer",
        opener='So {hero} walked over trying to look casual and said, "Hello. I have brought peace, warmth, and also soup."',
        style="that line",
        boldness=1,
        polite=True,
        sets_down=False,
        humor=True,
        tags={"flirt", "joke"},
    ),
    "plain_offer": Approach(
        id="plain_offer",
        opener='So {hero} walked over and said, "Hi. You looked cold, and I thought you might like some soup."',
        style="that",
        boldness=0,
        polite=True,
        sets_down=False,
        humor=False,
        tags={"flirt", "plain"},
    ),
    "bench_first": Approach(
        id="bench_first",
        opener='So {hero} set the bowl on the bench first and called, "For whenever you are done. No rush."',
        style="bench-first flirting",
        boldness=0,
        polite=True,
        sets_down=True,
        humor=False,
        tags={"flirt", "bench"},
    ),
    "too_bright": Approach(
        id="too_bright",
        opener='So {hero} hurried over and blurted, "Soup for the town\'s bravest archer!"',
        style="that compliment",
        boldness=2,
        polite=True,
        sets_down=False,
        humor=True,
        tags={"flirt", "compliment"},
    ),
}
@dataclass
class StoryParams:
    venue: str
    soup: str
    task: str
    support: str
    approach: str
    hero_name: str = "Mina"
    hero_type: str = "girl"
    archer_name: str = "Rowan"
    archer_type: str = "man"
    friend_name: str = "Tess"
    friend_type: str = "girl"
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        venue="hall",
        soup="tomato",
        task="resting",
        support="tray",
        approach="joke_offer",
        hero_name="Mina",
        hero_type="girl",
        archer_name="Rowan",
        archer_type="man",
        friend_name="Tess",
        friend_type="girl",
    ),
    StoryParams(
        venue="market",
        soup="noodle",
        task="practicing",
        support="tray",
        approach="bench_first",
        hero_name="June",
        hero_type="girl",
        archer_name="Evan",
        archer_type="man",
        friend_name="Nia",
        friend_type="girl",
    ),
    StoryParams(
        venue="gym",
        soup="pumpkin",
        task="scoring",
        support="board",
        approach="plain_offer",
        hero_name="Pia",
        hero_type="girl",
        archer_name="Leo",
        archer_type="man",
        friend_name="Mara",
        friend_type="girl",
    ),
    StoryParams(
        venue="hall",
        soup="tomato",
        task="packing",
        support="board",
        approach="too_bright",
        hero_name="Nora",
        hero_type="girl",
        archer_name="Finn",
        archer_type="man",
        friend_name="Ivy",
        friend_type="girl",
    ),
]


KNOWLEDGE = {
    "soup": [
        (
            "Why can soup spill easily?",
            "Soup is liquid, so it moves when you move the bowl. If a bowl tips or wobbles, the soup can slosh right over the edge.",
        )
    ],
    "archer": [
        (
            "What does an archer do?",
            "An archer uses a bow to shoot arrows at a target. Good archers stay very still and pay close attention when they aim.",
        )
    ],
    "tray": [
        (
            "Why does a tray help when you carry food?",
            "A tray gives the bowl a flatter, steadier place to sit. That makes it easier to keep the food from tipping.",
        )
    ],
    "napkin": [
        (
            "Can a napkin hold a bowl steady like a tray can?",
            "Not very well. A napkin can protect your hands a little, but it does not keep a bowl as steady as a tray does.",
        )
    ],
    "flirt": [
        (
            "What does flirt mean in a gentle story?",
            "Here it means trying to show someone you like them in a light, playful way. It should feel kind and respectful, not pushy.",
        )
    ],
    "joke": [
        (
            "Why can a joke make an awkward moment easier?",
            "A kind joke lets both people relax and share the same moment. Laughing together can turn embarrassment into warmth.",
        )
    ],
}
KNOWLEDGE_ORDER = ["soup", "archer", "tray", "napkin", "flirt", "joke"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    archer = world.facts["archer"]
    soup = world.facts["soup"]
    task = world.facts["task"]
    return [
        f'Write a slice-of-life story with gentle humor where someone tries to flirt by carrying {soup.label} to an archer.',
        f"Tell a cozy story set at {world.venue.place} where {hero.id} notices {archer.id} {task.action} and overthinks every step.",
        'Write a small everyday story with inner monologue, the words "flirt", "soup", and "archer", and an ending that feels warm instead of dramatic.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    archer = world.facts["archer"]
    soup = world.facts["soup"]
    task = world.facts["task"]
    support = world.facts["support"]
    approach = world.facts["approach"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who is helping serve soup, and {archer.id}, an archer nearby. The whole story grows out of one small, brave walk across the room.",
        ),
        (
            f"Why did {hero.id} walk over to {archer.id}?",
            f"{hero.id} wanted to flirt in a gentle way, so {hero.pronoun()} brought {archer.id} some {soup.label}. The soup gave {hero.pronoun('object')} a reason to start talking without pretending the moment was grander than it was.",
        ),
        (
            f"Why did {hero.id} think so hard before crossing the room?",
            f"{hero.pronoun().capitalize()} was nervous and kept talking to {hero.pronoun('object')}self in {hero.pronoun('possessive')} head. That inner monologue makes the scene funny because every tiny choice feels huge to {hero.pronoun('object')}.",
        ),
    ]
    if world.facts.get("wobble_happened"):
        qa.append(
            (
                "What was the risky moment in the middle of the story?",
                f"The risky moment came when {hero.id} approached while {archer.id} was {task.action}, and the bowl wobbled. It almost became a spill instead of a flirt.",
            )
        )
    if world.facts.get("support_saved"):
        qa.append(
            (
                f"How did {support.label} help?",
                f"The {support.label} kept the bowl steadier when {hero.id} got flustered. Because of that, the soup stayed in the bowl and the conversation could still happen.",
            )
        )
    if outcome == "shared_lunch":
        qa.append(
            (
                "How did the story end?",
                f"It ended with the two of them sharing a quiet bench and a real conversation. The ending proves the little risk was worth it because the moment becomes easy and ordinary instead of embarrassing.",
            )
        )
    elif outcome == "saved_face":
        qa.append(
            (
                "Did the flirt work perfectly?",
                f"No, not perfectly, but it worked kindly. The awkward wobble turned into a shared joke, and that made the ending feel warm anyway.",
            )
        )
    else:
        qa.append(
            (
                "Was the ending sad?",
                f"No. {hero.id} felt embarrassed for a moment, but {archer.id} answered with kindness later. The story ends with more courage than fear because {hero.id} is ready to try again better next time.",
            )
        )
    qa.append(
        (
            f"What kind of approach did {hero.id} use?",
            f"{hero.pronoun().capitalize()} used {approach.style}. That choice shaped whether the moment felt playful, calm, or a little too bright.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"soup", "archer", "flirt"}
    tags |= set(world.facts["support"].tags)
    tags |= set(world.facts["approach"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules={sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_support(soup: Soup, support: Support) -> str:
    return (
        f"(No story: {soup.label} needs support strength {support_needed(soup)}, "
        f"but {support.label} only provides {support.steady}. The bowl would be too wobbly to make a reasonable flirt scene.)"
    )


def explain_approach(task: ArcherTask, approach: Approach) -> str:
    return (
        f"(No story: during {task.action}, the archer has no hands free for {approach.id.replace('_', ' ')}. "
        f"Use an approach that sets the soup down first, or pick a less busy task.)"
    )


ASP_RULES = r"""
needs_support(S, N) :- soup(S), slosh(S, A), heat(S, B), N = A + B.
support_ok(S, P) :- needs_support(S, N), support(P), steady(P, V), V >= N.

approach_possible(T, A) :- task(T), approach(A), hands_free(T, H), H > 0.
approach_possible(T, A) :- task(T), approach(A), sets_down(A).

valid(V, S, T, P, A) :- venue(V), support_ok(S, P), approach_possible(T, A).

score(T, P, A, X) :- patience(T, PT), polite_bonus(P, PB), polite(A), boldness(A, B), X = PT + PB + 1 - B.
score(T, P, A, X) :- patience(T, PT), polite_bonus(P, PB), not polite(A), boldness(A, B), X = PT + PB - B.

outcome(shared_lunch) :- chosen_task(T), chosen_support(P), chosen_approach(A), can_chat_now(T), score(T, P, A, X), X >= 1.
outcome(saved_face) :- chosen_support(P), steady(P, V), steady_min(M), V >= M, not outcome(shared_lunch).
outcome(awkward_exit) :- not outcome(shared_lunch), not outcome(saved_face).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id in VENUES:
        lines.append(asp.fact("venue", venue_id))
    for soup_id, soup in SOUPS.items():
        lines.append(asp.fact("soup", soup_id))
        lines.append(asp.fact("slosh", soup_id, soup.slosh))
        lines.append(asp.fact("heat", soup_id, soup.heat))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("hands_free", task_id, task.hands_free))
        lines.append(asp.fact("patience", task_id, task.patience))
        if task.can_chat_now:
            lines.append(asp.fact("can_chat_now", task_id))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("steady", support_id, support.steady))
        lines.append(asp.fact("polite_bonus", support_id, support.polite_bonus))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("boldness", approach_id, approach.boldness))
        if approach.polite:
            lines.append(asp.fact("polite", approach_id))
        if approach.sets_down:
            lines.append(asp.fact("sets_down", approach_id))
    lines.append(asp.fact("steady_min", STEADY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_task", params.task),
            asp.fact("chosen_support", params.support),
            asp.fact("chosen_approach", params.approach),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos() matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    parser = build_parser()
    cases: list[StoryParams] = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

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
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Cozy story world: a soup-table flirt with an archer, told with humor and inner monologue."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--soup", choices=SOUPS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--hero-name")
    ap.add_argument("--archer-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Mina", "June", "Pia", "Nora", "Ivy", "Lena", "Tara", "Suki"]
BOY_NAMES = ["Rowan", "Evan", "Leo", "Finn", "Miles", "Jonah", "Owen", "Silas"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.soup and args.support:
        soup = SOUPS[args.soup]
        support = SUPPORTS[args.support]
        if not support_ok(soup, support):
            raise StoryError(explain_support(soup, support))
    if args.task and args.approach:
        task = TASKS[args.task]
        approach = APPROACHES[args.approach]
        if not approach_possible(task, approach):
            raise StoryError(explain_approach(task, approach))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.soup is None or combo[1] == args.soup)
        and (args.task is None or combo[2] == args.task)
        and (args.support is None or combo[3] == args.support)
        and (args.approach is None or combo[4] == args.approach)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue, soup, task, support, approach = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(GIRL_NAMES)
    archer_name = args.archer_name or rng.choice([n for n in BOY_NAMES if n != hero_name])
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES if n not in {hero_name}])
    return StoryParams(
        venue=venue,
        soup=soup,
        task=task,
        support=support,
        approach=approach,
        hero_name=hero_name,
        hero_type="girl",
        archer_name=archer_name,
        archer_type="man",
        friend_name=friend_name,
        friend_type="girl",
    )


def _filled_opener(approach: Approach, hero_name: str) -> Approach:
    return Approach(
        id=approach.id,
        opener=approach.opener.format(hero=hero_name),
        style=approach.style,
        boldness=approach.boldness,
        polite=approach.polite,
        sets_down=approach.sets_down,
        humor=approach.humor,
        tags=set(approach.tags),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        venue = VENUES[params.venue]
        soup = SOUPS[params.soup]
        task = TASKS[params.task]
        support = SUPPORTS[params.support]
        approach = APPROACHES[params.approach]
    except KeyError as err:
        raise StoryError(f"(Unknown option: {err.args[0]})") from None

    if not valid_combo(soup, task, support, approach):
        if not support_ok(soup, support):
            raise StoryError(explain_support(soup, support))
        raise StoryError(explain_approach(task, approach))

    world = tell(
        venue=venue,
        soup=soup,
        task=task,
        support=support,
        approach=_filled_opener(approach, params.hero_name),
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        archer_name=params.archer_name,
        archer_type=params.archer_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
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
        print(f"{len(combos)} valid (venue, soup, task, support, approach) combos:\n")
        for venue, soup, task, support, approach in combos:
            print(f"  {venue:7} {soup:8} {task:10} {support:7} {approach}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name} -> {p.archer_name}: {p.soup}, {p.task}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
