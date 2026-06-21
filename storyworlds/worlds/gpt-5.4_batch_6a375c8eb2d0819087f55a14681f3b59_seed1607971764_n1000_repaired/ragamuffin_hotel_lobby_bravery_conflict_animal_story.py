#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ragamuffin_hotel_lobby_bravery_conflict_animal_story.py
==================================================================================

A standalone story world about a ragamuffin kitten in a hotel lobby who faces a
small conflict, chooses bravery, and helps a lost animal guest.

The domain is deliberately narrow: a fluffy little lobby kitten notices that a
tiny animal has become separated from a parent in the busy hotel lobby. A real
obstacle stands between them and the front desk or waiting chair, and the kitten
must use the right helpful object or route to get through safely. A snippy
onlooker raises the conflict; a calm clerk encourages the kitten; the ending
shows that bravery changed how the lobby sees the kitten.

Run it
------
    python storyworlds/worlds/gpt-5.4/ragamuffin_hotel_lobby_bravery_conflict_animal_story.py
    python storyworlds/worlds/gpt-5.4/ragamuffin_hotel_lobby_bravery_conflict_animal_story.py --obstacle suitcase_rush
    python storyworlds/worlds/gpt-5.4/ragamuffin_hotel_lobby_bravery_conflict_animal_story.py --method tiny_towel
    python storyworlds/worlds/gpt-5.4/ragamuffin_hotel_lobby_bravery_conflict_animal_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/ragamuffin_hotel_lobby_bravery_conflict_animal_story.py --verify
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
        female = {"girl", "mother", "hen", "doe", "queen"}
        male = {"boy", "father", "drake", "buck", "king"}
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
class LostGuest:
    id: str
    label: str
    parent_label: str
    cry: str
    waiting_spot: str
    reunion_action: str
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
class Obstacle:
    id: str
    label: str
    scene: str
    problem: str
    danger_word: str
    challenge: str
    severity: int
    pass_text: str
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
class Method:
    id: str
    label: str
    offer: str
    action: str
    challenge: str
    support: int
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


@dataclass
class Doubter:
    id: str
    label: str
    speech: str
    lesson: str
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


def _r_separation(world: World) -> list[str]:
    guest = world.get("guest")
    parent = world.get("parent")
    if guest.meters["separated"] >= THRESHOLD:
        sig = ("separation", guest.id)
        if sig not in world.fired:
            world.fired.add(sig)
            guest.memes["fear"] += 1
            parent.memes["worry"] += 1
    return []


def _r_conflict(world: World) -> list[str]:
    hero = world.get("hero")
    doubter = world.get("doubter")
    if hero.memes["duty"] >= THRESHOLD and doubter.memes["taunt"] >= THRESHOLD:
        sig = ("conflict", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] += 1
    return []


def _r_reunion(world: World) -> list[str]:
    guest = world.get("guest")
    parent = world.get("parent")
    hero = world.get("hero")
    if guest.meters["with_parent"] >= THRESHOLD:
        sig = ("reunion", guest.id)
        if sig not in world.fired:
            world.fired.add(sig)
            guest.memes["relief"] += 1
            parent.memes["relief"] += 1
            parent.memes["worry"] = 0.0
            hero.memes["pride"] += 1
            hero.memes["belonging"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="separation", tag="social", apply=_r_separation),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="reunion", tag="social", apply=_r_reunion),
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
        for line in produced:
            world.say(line)
    return produced


def compatible_method(obstacle: Obstacle, method: Method) -> bool:
    return obstacle.challenge == method.challenge


def strong_enough(obstacle: Obstacle, method: Method) -> bool:
    return method.support >= obstacle.severity


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for obstacle_id, obstacle in OBSTACLES.items():
        for method_id, method in METHODS.items():
            if compatible_method(obstacle, method) and strong_enough(obstacle, method):
                combos.append((obstacle_id, method_id))
    return sorted(combos)


def explain_rejection(obstacle: Obstacle, method: Method) -> str:
    if not compatible_method(obstacle, method):
        return (
            f"(No story: {method.label} does not solve {obstacle.label}. "
            f"The obstacle is about {obstacle.danger_word}, but that method is for "
            f"{method.challenge}. Pick a method that truly fits the danger.)"
        )
    return (
        f"(No story: {method.label} fits {obstacle.label}, but it is too weak for this case. "
        f"The world wants a believable brave success, so choose a sturdier method.)"
    )


def outcome_of(params: "StoryParams") -> str:
    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    return "reunited" if compatible_method(obstacle, method) and strong_enough(obstacle, method) else "stuck"


def predict_help(world: World, obstacle_id: str, method_id: str) -> dict:
    obstacle = OBSTACLES[obstacle_id]
    method = METHODS[method_id]
    return {
        "fits": compatible_method(obstacle, method),
        "works": strong_enough(obstacle, method),
        "severity": obstacle.severity,
        "support": method.support,
    }


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"In the hotel lobby, a small ragamuffin kitten named {hero.id} liked to sit "
        f"beside the umbrella stand and watch the shiny day come and go."
    )
    world.say(
        "The floor gleamed, the brass lamp glowed, and the big clock above the front desk "
        "made each minute sound important."
    )


def establish_kindness(world: World, hero: Entity) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.id} was fluffy in a crooked, windy way, as if every nap had been taken in a hurry, "
        "but the kitten always noticed who needed a kind look."
    )


def discover_guest(world: World, hero: Entity, guest: Entity, guest_cfg: LostGuest, parent: Entity) -> None:
    guest.meters["separated"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That afternoon, a tiny {guest_cfg.label} stood near the potted palm and squeaked, "
        f'"{guest_cfg.cry}"'
    )
    world.say(
        f"{hero.id} spotted {guest.pronoun('object')} at once and saw {parent.label} "
        f"far across the lobby at {guest_cfg.waiting_spot}."
    )


def present_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["fear"] += 1
    world.say(obstacle.scene)
    world.say(
        f"{hero.id} wanted to help, but {obstacle.problem}. The thought of that {obstacle.danger_word} "
        "made the kitten's paws feel small."
    )


def volunteer(world: World, hero: Entity, guest_cfg: LostGuest) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'"Don\'t worry," {hero.id} whispered to the little {guest_cfg.label}. '
        f'"I will help you get back to {guest_cfg.parent_label}."'
    )


def taunt(world: World, hero: Entity, doubter: Entity, doubter_cfg: Doubter) -> None:
    doubter.memes["taunt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {doubter.label}, who had been lounging near the luggage rack, gave a sniff. "
        f'"{doubter_cfg.speech}"'
    )
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s ears dipped. The kitten did feel scruffy and small, and for one long moment "
            "the brave idea and the scared idea tugged in opposite directions."
        )


def encourage(world: World, hero: Entity, method: Method) -> None:
    clerk = world.get("clerk")
    hero.memes["hope"] += 1
    world.say(
        f"Then {clerk.label}, the old turtle at the front desk, leaned over and said, "
        f'"Brave does not mean big. {method.offer}."'
    )


def cross(world: World, hero: Entity, guest: Entity, obstacle: Obstacle, method: Method) -> None:
    pred = predict_help(world, obstacle.id, method.id)
    if not pred["fits"] or not pred["works"]:
        raise StoryError(explain_rejection(obstacle, method))
    hero.memes["bravery"] += float(method.support)
    hero.meters["crossed"] += 1
    hero.memes["conflict"] = max(0.0, hero.memes["conflict"] - 1.0)
    world.say(
        f"{hero.id} took a breath so deep that even the whiskers seemed to steady, and then "
        f"{method.action}. {obstacle.pass_text}"
    )
    world.say(
        f"The little {guest.label} hurried right beside the kitten, trusting those careful paws."
    )


def reunite(world: World, hero: Entity, guest: Entity, guest_cfg: LostGuest, parent: Entity) -> None:
    guest.meters["with_parent"] += 1
    guest.meters["separated"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"In another moment the {guest_cfg.label} reached {parent.label}, and {parent.pronoun()} "
        f"{guest_cfg.reunion_action}."
    )
    world.say(
        f'"Oh, thank you," {parent.label} said. "You were brave when my little one was frightened."'
    )


def changed_ending(world: World, hero: Entity, doubter_cfg: Doubter) -> None:
    doubter = world.get("doubter")
    hero.memes["joy"] += 1
    world.say(
        f"The snippy remark from {doubter.label} had nowhere to stay after that. Even {doubter.pronoun()} "
        f"murmured, \"{doubter_cfg.lesson}\""
    )
    world.say(
        f"When evening light turned the hotel lobby honey-gold, {hero.id} curled up again by the umbrella stand. "
        "Only now, when the wheels rattled or the doors whooshed, the guests did not call the kitten a ragamuffin "
        "in the unkind way. They called the kitten brave."
    )


def tell(
    guest_cfg: LostGuest,
    obstacle: Obstacle,
    method: Method,
    doubter_cfg: Doubter,
    hero_name: str = "Moppet",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type="kitten", label=hero_name, role="hero"))
    guest = world.add(Entity(id="guest", kind="character", type=guest_cfg.label, label=guest_cfg.label, role="guest"))
    parent = world.add(Entity(id="parent", kind="character", type="parent", label=guest_cfg.parent_label, role="parent"))
    clerk = world.add(Entity(id="clerk", kind="character", type="turtle", label="Toma the turtle clerk", role="clerk"))
    doubter = world.add(Entity(id="doubter", kind="character", type="poodle", label=doubter_cfg.label, role="doubter"))

    world.facts.update(
        hero=hero,
        guest=guest,
        parent=parent,
        clerk=clerk,
        doubter=doubter,
        guest_cfg=guest_cfg,
        obstacle=obstacle,
        method=method,
        doubter_cfg=doubter_cfg,
    )

    introduce(world, hero)
    establish_kindness(world, hero)

    world.para()
    discover_guest(world, hero, guest, guest_cfg, parent)
    present_obstacle(world, hero, obstacle)
    volunteer(world, hero, guest_cfg)
    taunt(world, hero, doubter, doubter_cfg)
    encourage(world, hero, method)

    world.para()
    cross(world, hero, guest, obstacle, method)
    reunite(world, hero, guest, guest_cfg, parent)

    world.para()
    changed_ending(world, hero, doubter_cfg)

    world.facts.update(
        predicted=predict_help(world, obstacle.id, method.id),
        outcome="reunited",
        reunion=True,
        brave=hero.memes["bravery"] >= float(obstacle.severity),
    )
    return world


GUESTS = {
    "duckling": LostGuest(
        id="duckling",
        label="duckling",
        parent_label="the worried duck mother",
        cry="Mama? Mama?",
        waiting_spot="the check-in line",
        reunion_action="swept one wing around the little duckling at once",
        tags={"duckling", "family"},
    ),
    "mouse": LostGuest(
        id="mouse",
        label="mouse child",
        parent_label="the worried mouse father",
        cry="Papa? Where are you?",
        waiting_spot="the blue velvet chair by the desk",
        reunion_action="wrapped a neat little tail around the mouse child in relief",
        tags={"mouse", "family"},
    ),
    "gosling": LostGuest(
        id="gosling",
        label="gosling",
        parent_label="the worried goose aunt",
        cry="Auntie! Auntie!",
        waiting_spot="the brass key shelf",
        reunion_action="bent a long neck down and tucked the gosling close",
        tags={"gosling", "family"},
    ),
    "bunny": LostGuest(
        id="bunny",
        label="bunny",
        parent_label="the worried rabbit mother",
        cry="Mama, I got turned around!",
        waiting_spot="the flowered sofa near the desk",
        reunion_action="gathered the bunny into a soft, trembling hug",
        tags={"bunny", "family"},
    ),
}

OBSTACLES = {
    "marble_puddle": Obstacle(
        id="marble_puddle",
        label="the slick marble puddle",
        scene="Rain had blown in from the front doors, leaving a silver puddle on the marble between the palm and the desk.",
        problem="one wrong step could send the pair sliding",
        danger_word="slippery marble",
        challenge="slip",
        severity=2,
        pass_text="Step by step, the kitten and the little guest crossed the wet shine without skidding once.",
        tags={"hotel_lobby", "puddle", "marble"},
    ),
    "suitcase_rush": Obstacle(
        id="suitcase_rush",
        label="the suitcase rush",
        scene="A family had just arrived, and rolling suitcases hummed and zigzagged across the lobby like a river with wheels.",
        problem="the little guest could be bumped before reaching the desk",
        danger_word="busy traffic",
        challenge="traffic",
        severity=3,
        pass_text="Suitcases swished by, but the brave route carried them safely through the noisy stream.",
        tags={"hotel_lobby", "suitcase", "busy"},
    ),
    "tall_counter": Obstacle(
        id="tall_counter",
        label="the tall front desk",
        scene="The front desk stood so high and polished that a tiny child at floor level could hardly be seen from the other side.",
        problem="calling from below would never reach the grown-up quickly",
        danger_word="being too small to be seen",
        challenge="height",
        severity=2,
        pass_text="From the higher spot, the lost little one could finally be seen clearly over the smooth desk edge.",
        tags={"hotel_lobby", "desk", "height"},
    ),
    "door_draft": Obstacle(
        id="door_draft",
        label="the swirling door draft",
        scene="Each time the grand front doors opened, a gust rolled through the hotel lobby and ruffled napkins, feathers, and fur.",
        problem="the tiny guest kept flinching backward from the swirl",
        danger_word="a strong draft",
        challenge="draft",
        severity=3,
        pass_text="The gusts still swirled, but the careful shelter let them move through without being blown apart.",
        tags={"hotel_lobby", "doors", "wind"},
    ),
}

METHODS = {
    "runner_rug": Method(
        id="runner_rug",
        label="the red runner rug",
        offer="Take the red runner rug from the coat stand and make a dry path",
        action="the kitten tugged the red runner rug across the wet floor and padded over it with the little guest tucked close",
        challenge="slip",
        support=2,
        qa_text="made a dry path with the red runner rug",
        tags={"rug", "safety"},
    ),
    "bell_cart": Method(
        id="bell_cart",
        label="the brass bell cart",
        offer="Use the brass bell cart and roll along the quiet edge of the lobby",
        action="the kitten hopped onto the brass bell cart, helped the little guest up, and nudged it along the quiet edge of the room",
        challenge="traffic",
        support=3,
        qa_text="used the brass bell cart to get through the suitcase traffic",
        tags={"bell_cart", "hotel"},
    ),
    "footstool": Method(
        id="footstool",
        label="the brass footstool",
        offer="Set the brass footstool by the desk so the little one can be seen",
        action="the kitten dragged over the brass footstool and stood beside it until the little guest climbed up",
        challenge="height",
        support=2,
        qa_text="brought over a brass footstool so the little one could be seen",
        tags={"stool", "desk"},
    ),
    "screen_walk": Method(
        id="screen_walk",
        label="the folding screen path",
        offer="Walk behind the folding screen where the wind cannot shove so hard",
        action="the kitten guided the little guest behind a folding screen and moved with the draft on one side and the wall on the other",
        challenge="draft",
        support=3,
        qa_text="used the folding screen as a calm path out of the wind",
        tags={"screen", "wind"},
    ),
    "tiny_towel": Method(
        id="tiny_towel",
        label="the tiny towel",
        offer="Take this tiny towel",
        action="the kitten spread a tiny towel on the floor and tried to step over it",
        challenge="slip",
        support=1,
        qa_text="tried to use a tiny towel",
        tags={"towel"},
    ),
    "polite_wave": Method(
        id="polite_wave",
        label="a polite wave",
        offer="Wave politely from where you are",
        action="the kitten gave a very polite wave from far away",
        challenge="height",
        support=1,
        qa_text="tried waving politely",
        tags={"wave"},
    ),
}

DOUBTERS = {
    "poodle": Doubter(
        id="poodle",
        label="Pip the poodle",
        speech="You? You are only a ragamuffin little lobby kitten. Leave important helping to somebody grand.",
        lesson="I was wrong. Small paws can still be brave.",
    ),
    "magpie": Doubter(
        id="magpie",
        label="Mina the magpie",
        speech="That looks much too difficult for a rumpled kitten. Better stay by the umbrella stand.",
        lesson="Well now. Brave is brighter than shiny feathers.",
    ),
    "ferret": Doubter(
        id="ferret",
        label="Nip the ferret",
        speech="You will only make a muddle of it, fluff-ball. Let someone bigger try.",
        lesson="I suppose courage can come in a scruffy coat.",
    ),
}

HERO_NAMES = ["Moppet", "Tuft", "Pipkin", "Buttons", "Soot", "Patches"]


@dataclass
class StoryParams:
    guest: str
    obstacle: str
    method: str
    doubter: str
    hero_name: str
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
    "ragamuffin": [
        (
            "What does ragamuffin mean?",
            "Ragamuffin can mean someone looks rumpled or a little untidy. It can also be the name of a very fluffy, gentle kind of cat."
        )
    ],
    "hotel_lobby": [
        (
            "What is a hotel lobby?",
            "A hotel lobby is the big front room near the entrance and front desk. Guests come there to check in, wait, and ask for help."
        )
    ],
    "bell_cart": [
        (
            "What is a bell cart?",
            "A bell cart is a rolling cart in a hotel for carrying bags. Because it moves on wheels, it can also help carry things safely across a busy lobby."
        )
    ],
    "puddle": [
        (
            "Why is a puddle slippery on marble?",
            "Water on smooth marble makes the floor slick. Feet can slide because there is less grip."
        )
    ],
    "desk": [
        (
            "Why might a tall desk be hard for a tiny child?",
            "If a desk is very tall, a small child may not be seen from the other side. Standing on something safe can help a grown-up notice them."
        )
    ],
    "wind": [
        (
            "Why can a strong draft bother a tiny animal?",
            "A draft is moving air. For a very small animal, a strong draft can feel pushy and scary."
        )
    ],
    "family": [
        (
            "Why do lost children feel scared?",
            "Children feel safer when they know where their grown-up is. When they get separated, they can feel worried until they are found again."
        )
    ],
    "safety": [
        (
            "What does bravery mean?",
            "Bravery does not mean having no fear. It means doing the kind and careful thing even when you feel scared."
        )
    ],
}
KNOWLEDGE_ORDER = ["ragamuffin", "hotel_lobby", "family", "puddle", "bell_cart", "desk", "wind", "safety"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    guest = f["guest_cfg"]
    obstacle = f["obstacle"]
    method = f["method"]
    hero = f["hero"]
    return [
        'Write a short Animal Story for a 3-to-5-year-old set in a hotel lobby that includes the word "ragamuffin" and centers on bravery.',
        f"Tell a gentle story about a ragamuffin kitten named {hero.label} who helps a lost {guest.label} across {obstacle.label} in a hotel lobby.",
        f"Write a small conflict-and-courage story where a doubter says the kitten is too scruffy to help, but the kitten uses {method.label} and proves otherwise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guest_cfg = f["guest_cfg"]
    parent = f["parent"]
    obstacle = f["obstacle"]
    method = f["method"]
    doubter = f["doubter"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a little ragamuffin kitten in the hotel lobby. The kitten notices a lost {guest_cfg.label} and decides to help."
        ),
        (
            f"Why was the little {guest_cfg.label} upset?",
            f"The little {guest_cfg.label} had become separated from {parent.label}. That is why the child was calling out and feeling frightened."
        ),
        (
            "What was the conflict in the middle of the story?",
            f"The conflict came from two directions at once: {obstacle.problem}, and {doubter.label} said the kitten was too small and scruffy to help. That made bravery feel harder, because the kitten had to push past fear and unkind words."
        ),
        (
            f"How did {hero.label} solve the problem?",
            f"{hero.label} {method.qa_text}. That fit the danger in the lobby and gave the little one a safe way to reach {parent.label}."
        ),
        (
            f"Why was {hero.label} brave?",
            f"{hero.label} felt scared and heard a mean, doubtful remark, but still chose to help. That is bravery, because the kitten did the kind and careful thing even while feeling small."
        ),
        (
            "How did the story end?",
            f"The lost child was reunited with {parent.label}, and the hotel lobby felt warm again. By the end, the guests saw the ragamuffin kitten as brave instead of shabby."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ragamuffin", "safety"}
    f = world.facts
    tags |= set(f["guest_cfg"].tags)
    tags |= set(f["obstacle"].tags)
    tags |= set(f["method"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        guest="duckling",
        obstacle="marble_puddle",
        method="runner_rug",
        doubter="poodle",
        hero_name="Moppet",
    ),
    StoryParams(
        guest="mouse",
        obstacle="suitcase_rush",
        method="bell_cart",
        doubter="magpie",
        hero_name="Buttons",
    ),
    StoryParams(
        guest="gosling",
        obstacle="tall_counter",
        method="footstool",
        doubter="ferret",
        hero_name="Tuft",
    ),
    StoryParams(
        guest="bunny",
        obstacle="door_draft",
        method="screen_walk",
        doubter="poodle",
        hero_name="Patches",
    ),
]


ASP_RULES = r"""
valid(O, M) :- obstacle(O), method(M), challenge(O, C), protects(M, C), support(M, S), severity(O, V), S >= V.
crossable(O, M) :- valid(O, M).
outcome(reunited) :- chosen_obstacle(O), chosen_method(M), crossable(O, M).
outcome(stuck) :- chosen_obstacle(O), chosen_method(M), not crossable(O, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("challenge", obstacle_id, obstacle.challenge))
        lines.append(asp.fact("severity", obstacle_id, obstacle.severity))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("protects", method_id, method.challenge))
        lines.append(asp.fact("support", method_id, method.support))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure at seed {seed}.")
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a ragamuffin kitten finds courage in a hotel lobby."
    )
    ap.add_argument("--guest", choices=sorted(GUESTS))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--doubter", choices=sorted(DOUBTERS))
    ap.add_argument("--hero-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible obstacle/method pairs from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.method:
        obstacle = OBSTACLES[args.obstacle]
        method = METHODS[args.method]
        if (args.obstacle, args.method) not in valid_combos():
            raise StoryError(explain_rejection(obstacle, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.obstacle is None or combo[0] == args.obstacle)
        and (args.method is None or combo[1] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    obstacle_id, method_id = rng.choice(combos)
    guest_id = args.guest or rng.choice(sorted(GUESTS))
    doubter_id = args.doubter or rng.choice(sorted(DOUBTERS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)

    return StoryParams(
        guest=guest_id,
        obstacle=obstacle_id,
        method=method_id,
        doubter=doubter_id,
        hero_name=hero_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.guest not in GUESTS:
        raise StoryError(f"(Unknown guest: {params.guest})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.doubter not in DOUBTERS:
        raise StoryError(f"(Unknown doubter: {params.doubter})")

    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    if (params.obstacle, params.method) not in valid_combos():
        raise StoryError(explain_rejection(obstacle, method))

    world = tell(
        guest_cfg=GUESTS[params.guest],
        obstacle=obstacle,
        method=method,
        doubter_cfg=DOUBTERS[params.doubter],
        hero_name=params.hero_name,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (obstacle, method) pairs:\n")
        for obstacle_id, method_id in combos:
            print(f"  {obstacle_id:14} {method_id}")
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
            header = (
                f"### {sample.params.hero_name}: {sample.params.guest} / "
                f"{sample.params.obstacle} / {sample.params.method}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
