#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/backward_friendship_bravery_misunderstanding_pirate_tale.py
======================================================================================

A standalone story world about two friends playing pirates, a brave helper who
seems to be backing away, and a misunderstanding that is healed by action.

The tiny domain is deliberately narrow and state-driven:

* Two children build a pirate game.
* A treasure is blocked by one obstacle.
* One friend walks backward to fetch or position the right help.
* The other child misunderstands that movement as retreat.
* The helper proves their friendship and bravery by making the obstacle safe.
* The ending image shows both children crossing or climbing together.

The world model tracks physical meters (support, progress, reached_treasure) and
emotional memes (fear, hurt, trust, relief, friendship). Prose is rendered from
those state changes rather than by swapping nouns into one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/backward_friendship_bravery_misunderstanding_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/backward_friendship_bravery_misunderstanding_pirate_tale.py --setting backyard --obstacle bridge --method rope
    python storyworlds/worlds/gpt-5.4/backward_friendship_bravery_misunderstanding_pirate_tale.py --setting beach --method crate
    python storyworlds/worlds/gpt-5.4/backward_friendship_bravery_misunderstanding_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/backward_friendship_bravery_misunderstanding_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/backward_friendship_bravery_misunderstanding_pirate_tale.py --verify
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
TRUST_STEADY = 7


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    id: str
    place: str
    scene: str
    rig: str
    afford_obstacles: set[str] = field(default_factory=set)
    afford_methods: set[str] = field(default_factory=set)
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
    the: str
    goal: str
    hazard: str
    danger_line: str
    difficulty: int
    success_image: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class HelpMethod:
    id: str
    label: str
    phrase: str
    action_gerund: str
    backward_line: str
    setup_text: str
    support_for: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_needs_help(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    hero = world.get("hero")
    if obstacle.meters["support"] >= THRESHOLD:
        return []
    sig = ("needs_help", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return ["__needs_help__"]


def _r_support_clears_path(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["support"] < THRESHOLD:
        return []
    sig = ("path_clear", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["passable"] += 1
    return ["__path_clear__"]


def _r_progress(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    hero = world.get("hero")
    friend = world.get("friend")
    if obstacle.meters["passable"] < THRESHOLD:
        return []
    if hero.meters["progress"] >= THRESHOLD:
        return []
    sig = ("progress", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    courage = hero.memes["bravery"] + friend.memes["encouragement"]
    if courage >= obstacle.attrs["needed_courage"]:
        hero.meters["progress"] += 1
        hero.meters["reached_treasure"] += 1
        hero.memes["relief"] += 1
        friend.memes["relief"] += 1
        hero.memes["friendship"] += 1
        friend.memes["friendship"] += 1
        return ["__reached__"]
    hero.memes["fear"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="needs_help", tag="physical", apply=_r_needs_help),
    Rule(name="support_clears_path", tag="physical", apply=_r_support_clears_path),
    Rule(name="progress", tag="physical", apply=_r_progress),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combo(setting_id: str, obstacle_id: str, method_id: str) -> bool:
    if setting_id not in SETTINGS or obstacle_id not in OBSTACLES or method_id not in METHODS:
        return False
    setting = SETTINGS[setting_id]
    method = METHODS[method_id]
    return obstacle_id in setting.afford_obstacles and method_id in setting.afford_methods and obstacle_id in method.support_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for obstacle_id in sorted(setting.afford_obstacles):
            for method_id in sorted(setting.afford_methods):
                if obstacle_id in METHODS[method_id].support_for:
                    combos.append((setting_id, obstacle_id, method_id))
    return combos


def outcome_of(trust: int) -> str:
    return "steady" if trust >= TRUST_STEADY else "misjudged"


def explain_rejection(setting_id: str, obstacle_id: str, method_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if obstacle_id not in OBSTACLES:
        return f"(No story: unknown obstacle '{obstacle_id}'.)"
    if method_id not in METHODS:
        return f"(No story: unknown method '{method_id}'.)"
    setting = SETTINGS[setting_id]
    if obstacle_id not in setting.afford_obstacles:
        return (
            f"(No story: {setting.place} does not plausibly contain {OBSTACLES[obstacle_id].the}. "
            f"Pick an obstacle that fits the play space.)"
        )
    if method_id not in setting.afford_methods:
        return (
            f"(No story: {METHODS[method_id].label} is not a plausible thing to use in {setting.place}. "
            f"Pick a helper object that belongs in that setting.)"
        )
    return (
        f"(No story: {METHODS[method_id].label} does not solve {OBSTACLES[obstacle_id].the}. "
        f"The helper must actually make the obstacle safer.)"
    )


def predict_support(world: World, obstacle_id: str, method_id: str) -> dict:
    sim = world.copy()
    obstacle = sim.get(obstacle_id)
    method = METHODS[method_id]
    if obstacle.id in method.support_for:
        obstacle.meters["support"] += 1
        propagate(sim, narrate=False)
    return {
        "passable": obstacle.meters["passable"] >= THRESHOLD,
        "hero_fear": sim.get("hero").memes["fear"],
    }


def pirate_setup(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    for kid in (hero, friend):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {friend.id} turned {setting.place} into {setting.scene}. "
        f"{setting.rig}"
    )
    world.say(
        f'"Captain {hero.id}!" {friend.id} cried. "And First Mate {friend.id}! '
        f"Today we find the hidden treasure." '"'
    )


def spot_goal(world: World, hero: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"Soon {hero.id} spotted {obstacle.goal}, but {obstacle.the} stood in the way. "
        f"{obstacle.danger_line}"
    )
    world.say(f'{hero.id} took one brave step, then stopped. "{obstacle.hazard}"')


def promise_help(world: World, friend: Entity, method: HelpMethod, obstacle: Obstacle) -> None:
    friend.memes["bravery"] += 1
    pred = predict_support(world, "obstacle", method.id)
    world.facts["predicted_passable"] = pred["passable"]
    world.say(
        f'{friend.id} squinted at {obstacle.the}. "Wait. I know a pirate way to help."'
    )


def backward_move(world: World, hero: Entity, friend: Entity, method: HelpMethod) -> None:
    friend.meters["distance"] += 1
    world.say(method.backward_line.format(friend=friend.id))
    if hero.memes["trust"] < TRUST_STEADY:
        hero.memes["hurt"] += 1
        hero.memes["fear"] += 1
        world.facts["misunderstood"] = True
        world.say(
            f"{hero.id}'s heart sank. From far away, it looked as if {friend.id} was backing out of the adventure."
        )
        world.say(
            f'"{friend.id}, don\'t leave me!" {hero.id} called. "I thought pirates were supposed to be brave together."'
        )
    else:
        world.facts["misunderstood"] = False
        hero.memes["confusion"] += 1
        world.say(
            f"For one puzzled moment, {hero.id} wondered why {friend.id} was going backward instead of forward."
        )


def reveal_help(world: World, hero: Entity, friend: Entity, obstacle: Entity, method: HelpMethod, obstacle_cfg: Obstacle) -> None:
    obstacle.meters["support"] += 1
    friend.meters["distance"] = 0
    friend.memes["encouragement"] += 1
    hero.memes["trust"] += 2
    hero.memes["relief"] += 1
    friend.memes["friendship"] += 1
    world.say(method.setup_text.format(friend=friend.id, obstacle=obstacle_cfg.the))
    if world.facts.get("misunderstood"):
        hero.memes["hurt"] = 0.0
        world.say(
            f'Then {hero.id} saw the truth. {friend.id} had not run away at all. {friend.pronoun().capitalize()} had gone backward only to make the path safe.'
        )
    world.say(
        f'"I was never leaving," {friend.id} said. "I was helping from the other direction. Come on, Captain. I\'m with you."'
    )
    propagate(world, narrate=False)


def cross_together(world: World, hero: Entity, friend: Entity, obstacle_cfg: Obstacle, method: HelpMethod) -> None:
    hero.memes["bravery"] += 1
    friend.memes["encouragement"] += 1
    propagate(world, narrate=False)
    if hero.meters["reached_treasure"] < THRESHOLD:
        raise StoryError("(Internal story error: the help did not make the goal reachable.)")
    world.say(
        f"{hero.id} took a deep breath and tried again. This time {friend.id}'s steady voice was like a hand on {hero.pronoun('possessive')} shoulder."
    )
    world.say(
        obstacle_cfg.success_image.format(hero=hero.id, friend=friend.id, method=method.label)
    )
    world.say(
        f"Together they reached the treasure first, and it felt even finer because they had reached it as friends."
    )


def mend_friendship(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f'When the prize was safe in their hands, {hero.id} looked at {friend.id} and whispered, "I was wrong about you."'
    )
    world.say(
        f'"That\'s all right," {friend.id} said. "Sometimes brave things look backward before they go forward."'
    )
    world.say(
        f"They bumped shoulders like true shipmates, and the misunderstanding drifted away like a paper boat on a puddle."
    )


def bright_ending(world: World, hero: Entity, friend: Entity, setting: Setting, obstacle: Obstacle) -> None:
    world.say(
        f"Before sunset, the two pirates sailed their game on through {setting.place}. "
        f"Now when they saw {obstacle.the}, they remembered not fear, but the moment friendship had made it small."
    )


def tell(
    setting: Setting,
    obstacle_cfg: Obstacle,
    method: HelpMethod,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    trust: int = 5,
) -> World:
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    obstacle = world.add(Entity(id="obstacle", type="obstacle", label=obstacle_cfg.label))
    treasure = world.add(Entity(id="treasure", type="treasure", label="treasure"))

    hero.attrs["name"] = hero_name
    friend.attrs["name"] = friend_name
    obstacle.attrs["needed_courage"] = float(obstacle_cfg.difficulty)

    hero.memes["trust"] = float(trust)
    hero.memes["bravery"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["hurt"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["friendship"] = 1.0
    friend.memes["bravery"] = 1.0
    friend.memes["encouragement"] = 0.0
    friend.memes["friendship"] = 1.0

    obstacle.meters["support"] = 0.0
    obstacle.meters["passable"] = 0.0
    hero.meters["progress"] = 0.0
    hero.meters["reached_treasure"] = 0.0
    friend.meters["distance"] = 0.0
    treasure.meters["claimed"] = 0.0

    world.facts["misunderstood"] = False
    world.facts["predicted_passable"] = False
    world.facts["trust_start"] = trust

    pirate_setup(world, hero, friend, setting)
    spot_goal(world, hero, obstacle_cfg)
    propagate(world, narrate=False)

    world.para()
    promise_help(world, friend, method, obstacle_cfg)
    backward_move(world, hero, friend, method)

    world.para()
    reveal_help(world, hero, friend, obstacle, method, obstacle_cfg)
    cross_together(world, hero, friend, obstacle_cfg, method)
    treasure.meters["claimed"] += 1

    world.para()
    mend_friendship(world, hero, friend)
    bright_ending(world, hero, friend, setting, obstacle_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        obstacle_cfg=obstacle_cfg,
        obstacle=obstacle,
        method=method,
        setting=setting,
        treasure=treasure,
        hero_name=hero_name,
        friend_name=friend_name,
        outcome=outcome_of(trust),
        reached=hero.meters["reached_treasure"] >= THRESHOLD,
        support=obstacle.meters["support"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        scene="a windy pirate cove",
        rig="The sandbox was their ship, a rake was their mast, and a blue blanket made a sea that slapped softly at the grass.",
        afford_obstacles={"bridge", "lookout"},
        afford_methods={"rope", "crate", "board"},
        tags={"yard", "pirates"},
    ),
    "beach": Setting(
        id="beach",
        place="the beach",
        scene="a bright island harbor",
        rig="A driftwood fort was their ship, shells were silver coins, and the tide pools looked like secret maps.",
        afford_obstacles={"bridge", "moat"},
        afford_methods={"rope", "board"},
        tags={"beach", "pirates"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        scene="a candle-free captain's cabin",
        rig="The sofa was their ship, pillows were barrel-casks, and a striped rug made a grand sea right across the floor.",
        afford_obstacles={"lookout", "moat"},
        afford_methods={"crate", "board"},
        tags={"indoors", "pirates"},
    ),
}

OBSTACLES = {
    "bridge": Obstacle(
        id="bridge",
        label="wobbly bridge",
        the="the wobbly bridge",
        goal="a bright tin-box treasure on the far side of the pretend water",
        hazard='"That bridge wiggles too much for my pirate feet."',
        danger_line="Each board gave a tiny knock and sway whenever the breeze touched it.",
        difficulty=2,
        success_image="{hero} crossed slowly while {friend} held the line tight, and the bridge stopped trembling under {hero}'s feet.",
        tags={"bridge", "crossing"},
    ),
    "lookout": Obstacle(
        id="lookout",
        label="high lookout",
        the="the high lookout",
        goal="a red captain's flag tucked up in the crow's-nest perch",
        hazard='"I can see the prize, but it is too high."',
        danger_line="The top perch looked wonderfully grand and a little too tall all at once.",
        difficulty=2,
        success_image="With {method} set firmly below, {hero} climbed to the perch while {friend} steadied everything from underneath.",
        tags={"height", "climbing"},
    ),
    "moat": Obstacle(
        id="moat",
        label="chalk-blue moat",
        the="the chalk-blue moat",
        goal="a shoebox chest waiting on the treasure island beyond the line",
        hazard='"If I jump and miss, I will splash straight into the pretend sharks."',
        danger_line="The blue chalk line was only pretend water, but in their game it looked deep enough for a whole sea-serpent.",
        difficulty=1,
        success_image="{friend} laid the way true, and {hero} marched over without even brushing the shark-water below.",
        tags={"moat", "crossing"},
    ),
}

METHODS = {
    "rope": HelpMethod(
        id="rope",
        label="rope line",
        phrase="a coil of rope",
        action_gerund="paying out a rope line",
        backward_line="{friend} hurried backward across the deck, letting a coil of rope slither after {friend.pronoun('object')}.",
        setup_text="{friend} planted {friend.pronoun('possessive')} feet, pulled the rope snug beside {obstacle}, and made a steady hand-line to hold.",
        support_for={"bridge", "moat"},
        tags={"rope", "help"},
    ),
    "crate": HelpMethod(
        id="crate",
        label="wooden crate",
        phrase="a wooden crate",
        action_gerund="dragging a wooden crate",
        backward_line="{friend} walked backward in little huffing steps, dragging a wooden crate from the corner of the ship.",
        setup_text="{friend} nudged the crate under {obstacle} until it sat firm and square, like a pirate step made just for climbing.",
        support_for={"lookout"},
        tags={"crate", "help"},
    ),
    "board": HelpMethod(
        id="board",
        label="long board",
        phrase="a long board",
        action_gerund="pulling a long board into place",
        backward_line="{friend} backed away so far that for a second only {friend.pronoun('possessive')} elbows showed, and then a long board scraped after {friend.pronoun('object')}.",
        setup_text="{friend} lowered the board across {obstacle} and pressed on both ends until it stopped wobbling.",
        support_for={"bridge", "moat", "lookout"},
        tags={"board", "help"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    method: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    trust: int = 5
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
    "backward": [
        (
            "What does backward mean?",
            "Backward means moving the opposite way from forward. If you walk backward, your feet step behind you while your face still points the other way.",
        )
    ],
    "friendship": [
        (
            "What makes someone a good friend?",
            "A good friend stays kind and helps when things get hard. A friend may not always look helpful at first, but good friendship shows itself in caring actions.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel scared. It does not mean never feeling fear; it means keeping your kind and steady heart.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what another person means, but gets it wrong. Talking and paying attention can help clear it up.",
        )
    ],
    "rope": [
        (
            "What can a rope help with?",
            "A rope can give your hands something steady to hold. That makes crossing or climbing feel safer.",
        )
    ],
    "board": [
        (
            "Why can a board help you cross a gap?",
            "A board can make a flat path over a space. If it is set firmly, it gives your feet a safer place to step.",
        )
    ],
    "crate": [
        (
            "How can a crate help someone reach something high?",
            "A strong crate can work like a step. It lifts you a little higher so you can climb or reach more safely.",
        )
    ],
    "bridge": [
        (
            "Why can a wobbly bridge feel scary?",
            "A wobbly bridge moves under your feet, so your body feels unsure where to balance. That shaky feeling can make even a brave child stop and think.",
        )
    ],
    "moat": [
        (
            "What is a moat in a pretend pirate game?",
            "A moat is a ring of water around a place that players imagine they must cross. In a game it may only be chalk or a blanket, but children still treat it like part of the adventure.",
        )
    ],
    "lookout": [
        (
            "What is a lookout place on a ship?",
            "A lookout is a high spot where a sailor can see far away. In pirate play, it is often the best place to spot treasure first.",
        )
    ],
}
KNOWLEDGE_ORDER = ["backward", "friendship", "bravery", "misunderstanding", "rope", "board", "crate", "bridge", "moat", "lookout"]


CURATED = [
    StoryParams(
        setting="backyard",
        obstacle="bridge",
        method="rope",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        trust=4,
    ),
    StoryParams(
        setting="playroom",
        obstacle="lookout",
        method="crate",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        trust=8,
    ),
    StoryParams(
        setting="beach",
        obstacle="moat",
        method="board",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        trust=5,
    ),
    StoryParams(
        setting="backyard",
        obstacle="lookout",
        method="board",
        hero_name="Sam",
        hero_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        trust=7,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    obstacle = f["obstacle_cfg"]
    method = f["method"]
    return [
        'Write a pirate-style story for a 3-to-5-year-old that uses the word "backward" and includes friendship, bravery, and a misunderstanding.',
        f"Tell a gentle pirate tale where {hero.attrs['name']} thinks {friend.attrs['name']} is backing away from {obstacle.the}, but {friend.attrs['name']} is really using {method.phrase} to help.",
        f"Write a small adventure where two friends reach treasure together after one child learns that brave help can sometimes begin by moving backward.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    obstacle = f["obstacle_cfg"]
    method = f["method"]
    hero_name = hero.attrs["name"]
    friend_name = friend.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {hero_name} and {friend_name}, pretending to be pirates. Their game becomes a real test of trust when treasure sits beyond {obstacle.the}.",
        ),
        (
            "What problem stopped the treasure hunt?",
            f"The treasure was there, but {obstacle.the} made the last part feel unsafe for {hero_name}. The obstacle mattered because {hero.pronoun('subject')} wanted to be brave but did not want to slip or miss.",
        ),
        (
            f"Why did {hero_name} think {friend_name} was leaving?",
            f"{friend_name} moved backward just when the problem looked hardest, so from far away it looked like retreat. {hero_name} misunderstood the movement because the helping tool was not visible yet.",
        ),
        (
            f"What was {friend_name} really doing?",
            f"{friend_name} was fetching and placing {method.phrase} to make the way safer. That action proved both bravery and friendship, because {friend.pronoun('subject')} kept helping even after being misunderstood.",
        ),
    ]
    if f["outcome"] == "misjudged":
        qa.append(
            (
                f"How was the misunderstanding fixed?",
                f"It was fixed when {hero_name} saw the help clearly and heard {friend_name} explain, \"I was never leaving.\" Seeing the safe path made the truth plain, so hurt feelings turned into relief.",
            )
        )
    else:
        qa.append(
            (
                f"Was {hero_name} sure from the start that {friend_name} would help?",
                f"Almost. {hero_name} felt puzzled for a moment, but trusted {friend_name} enough to wait and watch. That steady trust made the misunderstanding smaller and shorter.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with both friends reaching the treasure together and feeling closer than before. The ending image shows that the real prize was not only the treasure, but friendship made stronger by brave help.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"backward", "friendship", "bravery", "misunderstanding"}
    tags |= set(f["obstacle_cfg"].tags)
    tags |= set(f["method"].tags)
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
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {eid:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,M) :- setting(S), obstacle(O), method(M),
                affords_obstacle(S,O), affords_method(S,M), supports(M,O).

steady :- trust(T), trust_steady(K), T >= K.
misjudged :- trust(T), trust_steady(K), T < K.

outcome(steady) :- steady.
outcome(misjudged) :- misjudged.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for oid in sorted(setting.afford_obstacles):
            lines.append(asp.fact("affords_obstacle", sid, oid))
        for mid in sorted(setting.afford_methods):
            lines.append(asp.fact("affords_method", sid, mid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for oid in sorted(method.support_for):
            lines.append(asp.fact("supports", mid, oid))
    lines.append(asp.fact("trust_steady", TRUST_STEADY))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(trust: int) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("trust", trust), "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirates, a backward step, friendship, bravery, and a misunderstanding."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, obstacle, method) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle and args.method and not valid_combo(args.setting, args.obstacle, args.method):
        raise StoryError(explain_rejection(args.setting, args.obstacle, args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        if args.setting and args.obstacle and args.method:
            raise StoryError(explain_rejection(args.setting, args.obstacle, args.method))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    trust = args.trust if args.trust is not None else rng.randint(3, 9)

    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.obstacle, params.method):
        raise StoryError(explain_rejection(params.setting, params.obstacle, params.method))

    try:
        setting = SETTINGS[params.setting]
        obstacle = OBSTACLES[params.obstacle]
        method = METHODS[params.method]
    except KeyError as exc:
        raise StoryError(f"(No story: unknown parameter {exc!s}.)") from exc

    world = tell(
        setting=setting,
        obstacle_cfg=obstacle,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        trust=params.trust,
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
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: ASP gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in ASP:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in Python:", sorted(py_combos - asp_combos))

    trust_cases = list(range(0, 11))
    bad = [t for t in trust_cases if asp_outcome(t) != outcome_of(t)]
    if not bad:
        print(f"OK: ASP outcome matches Python on {len(trust_cases)} trust values.")
    else:
        rc = 1
        print("MISMATCH in outcome model for trust values:", bad)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: curated story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED on curated sample: {exc}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty random story.)")
        _ = sample.to_dict()
        print("OK: default/random generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED on default/random generation: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, method) combos:\n")
        for setting, obstacle, method in combos:
            print(f"  {setting:9} {obstacle:8} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name} & {p.friend_name}: {p.setting}, {p.obstacle}, {p.method} (trust {p.trust}, {outcome_of(p.trust)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
