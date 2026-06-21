#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/accurate_repetition_bravery_adventure.py
==================================================================

A standalone storyworld about a small adventure trail where one child feels
afraid, another child repeats an accurate guiding phrase, and bravery grows
enough for a real turn in the story. The domain is intentionally small and
constraint-checked: a place must actually contain the obstacle, and the chosen
guide must truly fit that obstacle.

Run it
------
    python storyworlds/worlds/gpt-5.4/accurate_repetition_bravery_adventure.py
    python storyworlds/worlds/gpt-5.4/accurate_repetition_bravery_adventure.py --place pine_trail --obstacle echo_tunnel --guide lantern_marks --repeats 3
    python storyworlds/worlds/gpt-5.4/accurate_repetition_bravery_adventure.py --guide guessing
    python storyworlds/worlds/gpt-5.4/accurate_repetition_bravery_adventure.py --all
    python storyworlds/worlds/gpt-5.4/accurate_repetition_bravery_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/accurate_repetition_bravery_adventure.py --verify
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
ACCURACY_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    goal: str
    goal_image: str
    affords: set[str] = field(default_factory=set)
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
    sight: str
    fear_need: int
    crossing: str
    safe_alt: str
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
class Guide:
    id: str
    label: str
    phrase: str
    supports: set[str] = field(default_factory=set)
    accuracy: int = 0
    courage_bonus: int = 0
    method: str = ""
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "repeat_lines": [],
            "predicted_success": False,
            "predicted_gap": 0,
        }

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


def _r_focus_from_repeat(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    guide = world.get("guide")
    repeats = int(world.facts.get("repeats", 0))
    if guide.attrs.get("accuracy", 0) < ACCURACY_MIN:
        return out
    done = int(hero.meters["focus_from_repeat"])
    while done < repeats:
        done += 1
        sig = ("focus", done)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["focus"] += 1
        hero.meters["focus_from_repeat"] += 1
        out.append("__focus__")
    return out


def _r_bravery_from_focus(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    while hero.meters["focus"] >= hero.meters["bravery_from_focus"] + 1:
        step = int(hero.meters["bravery_from_focus"] + 1)
        sig = ("bravery", step)
        if sig in world.fired:
            break
        world.fired.add(sig)
        hero.memes["bravery"] += 1
        hero.meters["bravery_from_focus"] += 1
        if obstacle.meters["fear"] > 0:
            obstacle.meters["fear"] -= 1
        out.append("__bravery__")
    return out


def _r_cross_if_ready(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    guide = world.get("guide")
    if guide.attrs.get("supports_obstacle") != obstacle.attrs.get("kind"):
        return []
    if guide.attrs.get("accuracy", 0) < ACCURACY_MIN:
        return []
    if hero.memes["bravery"] + guide.attrs.get("courage_bonus", 0) < obstacle.attrs.get("fear_need", 0):
        return []
    sig = ("cross", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["progress"] += 1
    obstacle.meters["crossed"] += 1
    return ["__crossed__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="focus_from_repeat", tag="emotional", apply=_r_focus_from_repeat),
    Rule(name="bravery_from_focus", tag="emotional", apply=_r_bravery_from_focus),
    Rule(name="cross_if_ready", tag="physical", apply=_r_cross_if_ready),
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


def usable_guide(guide: Guide, obstacle: Obstacle) -> bool:
    return obstacle.id in guide.supports and guide.accuracy >= ACCURACY_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id in place.affords:
            obstacle = OBSTACLES[obstacle_id]
            for guide_id, guide in GUIDES.items():
                if usable_guide(guide, obstacle):
                    combos.append((place_id, obstacle_id, guide_id))
    return sorted(combos)


def success_possible(obstacle: Obstacle, guide: Guide, repeats: int) -> bool:
    return usable_guide(guide, obstacle) and repeats + guide.courage_bonus >= obstacle.fear_need


def explain_rejection(place: Optional[Place], obstacle: Optional[Obstacle], guide: Optional[Guide]) -> str:
    if guide is not None and guide.accuracy < ACCURACY_MIN:
        better = ", ".join(sorted(gid for gid, g in GUIDES.items() if g.accuracy >= ACCURACY_MIN))
        return (
            f"(Refusing guide '{guide.id}': its directions are not accurate enough for this world. "
            f"Brave choices need accurate help. Try one of: {better}.)"
        )
    if place is not None and obstacle is not None and obstacle.id not in place.affords:
        return (
            f"(No story: {place.label} does not have {obstacle.label}, so the adventure cannot turn on that obstacle there.)"
        )
    if obstacle is not None and guide is not None and obstacle.id not in guide.supports:
        return (
            f"(No story: {guide.label} is not a sensible way to get past {obstacle.label}. "
            f"Pick a guide that truly fits the obstacle.)"
        )
    return "(No valid combination matches the given options.)"


def predict_crossing(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    obstacle = sim.get("obstacle")
    guide = sim.get("guide")
    total = hero.memes["bravery"] + guide.attrs.get("courage_bonus", 0)
    need = obstacle.attrs.get("fear_need", 0)
    return {
        "success": obstacle.meters["crossed"] >= THRESHOLD,
        "courage_total": total,
        "gap": max(0, need - total),
    }


def introduce(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"{hero.id} and {friend.id} set out along {place.opening}. They were not hunting monsters or gold. "
        f"They were hunting the little adventure waiting at {place.goal}."
    )


def find_goal(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{friend.id} pointed ahead and whispered, "
        f'"If we make it there before the light turns honey-colored, we can see everything from the top."'
    )


def meet_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    world.get("obstacle").meters["fear"] = float(obstacle.fear_need)
    hero.memes["fear"] += 1
    world.say(
        f"Then they reached {obstacle.label}. {obstacle.sight} For the first time that afternoon, "
        f"{hero.id}'s brave feet forgot how to move."
    )


def offer_guide(world: World, friend: Entity, hero: Entity, guide: Guide) -> None:
    pred = predict_crossing(world)
    world.facts["predicted_success"] = pred["success"]
    world.facts["predicted_gap"] = pred["gap"]
    world.say(
        f'{friend.id} did not laugh. {friend.pronoun().capitalize()} lifted {guide.label} and said, '
        f'"We do not need lucky guesses. We need accurate steps."'
    )
    world.say(
        f'{friend.id} showed {hero.id} how to {guide.method}. Then {friend.pronoun()} said, '
        f'"Say it with me."'
    )


def repeat_phrase(world: World, hero: Entity, friend: Entity, guide: Guide, repeats: int) -> None:
    world.facts["repeats"] = repeats
    lines: list[str] = []
    for i in range(repeats):
        line = guide.phrase
        lines.append(line)
        if i == 0:
            world.say(f'"{line}"')
        elif i == repeats - 1 and repeats > 1:
            world.say(f'"{line}" Again.')
        else:
            world.say(f'"{line}" Again.')
    world.facts["repeat_lines"] = lines
    propagate(world, narrate=False)
    if hero.memes["bravery"] >= THRESHOLD:
        world.say(
            f"Each careful repetition made the path feel smaller and clearer. {hero.id} could feel courage arriving one steady step at a time."
        )


def cross(world: World, hero: Entity, friend: Entity, obstacle: Obstacle, place: Place, prize: str) -> None:
    world.say(
        f"{hero.id} took a breath, followed the pattern, and crossed {obstacle.crossing}. "
        f"{friend.id} stayed close, repeating the words softly until both of them were through."
    )
    world.say(
        f"Beyond the obstacle, the trail opened wide. At {place.goal}, they found {prize} and stood very still, smiling at how big the world looked."
    )
    world.say(place.goal_image)


def retreat(world: World, hero: Entity, friend: Entity, obstacle: Obstacle, place: Place) -> None:
    hero.memes["good_judgment"] += 1
    friend.memes["good_judgment"] += 1
    world.say(
        f"{hero.id} tried one step, then stopped. {friend.id} saw the shake in {hero.pronoun('possessive')} hands and nodded."
    )
    world.say(
        f'"Brave does not mean rushing," {friend.id} said. "Brave can mean turning back before someone gets hurt."'
    )
    world.say(
        f"So they left {obstacle.label} behind and took {obstacle.safe_alt} instead. They did not reach {place.goal}, but they reached a sunny overlook and told the story of the trail as if they had brought back a secret."
    )


def closing_change(world: World, hero: Entity, guide: Guide, success: bool) -> None:
    if success:
        world.say(
            f"On the walk home, {hero.id} whispered the phrase once more -- not because {hero.pronoun()} was scared now, but because the accurate words had become a brave song."
        )
    else:
        world.say(
            f"On the walk home, {hero.id} repeated the phrase once more and promised to come back another day. The accurate words still mattered, because they had taught {hero.pronoun('object')} how real bravery sounds."
        )


def tell(
    place: Place,
    obstacle: Obstacle,
    guide: Guide,
    *,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    friend_name: str = "Finn",
    friend_gender: str = "boy",
    repeats: int = 3,
    prize: str = "a brass lookout bell",
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    obstacle_ent = world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label))
    guide_ent = world.add(Entity(id="guide", type="guide", label=guide.label))
    goal = world.add(Entity(id="goal", type="goal", label=place.goal))

    hero.memes["bravery"] = 0.0
    hero.memes["fear"] = 0.0
    hero.meters["focus"] = 0.0
    hero.meters["focus_from_repeat"] = 0.0
    hero.meters["bravery_from_focus"] = 0.0
    hero.meters["progress"] = 0.0

    friend.memes["care"] = 1.0

    obstacle_ent.attrs["kind"] = obstacle.id
    obstacle_ent.attrs["fear_need"] = obstacle.fear_need
    obstacle_ent.meters["fear"] = 0.0
    obstacle_ent.meters["crossed"] = 0.0

    guide_ent.attrs["kind"] = guide.id
    guide_ent.attrs["accuracy"] = guide.accuracy
    guide_ent.attrs["courage_bonus"] = guide.courage_bonus
    guide_ent.attrs["supports_obstacle"] = next(iter(guide.supports)) if guide.supports else ""

    world.facts.update(
        hero=hero,
        friend=friend,
        obstacle_cfg=obstacle,
        guide_cfg=guide,
        place=place,
        goal=goal,
        prize=prize,
        repeats=repeats,
    )

    introduce(world, hero, friend, place)
    find_goal(world, hero, friend)

    world.para()
    meet_obstacle(world, hero, obstacle)
    offer_guide(world, friend, hero, guide)
    repeat_phrase(world, hero, friend, guide, repeats)

    world.para()
    propagate(world, narrate=False)
    success = world.get("obstacle").meters["crossed"] >= THRESHOLD
    if success:
        cross(world, hero, friend, obstacle, place, prize)
    else:
        retreat(world, hero, friend, obstacle, place)

    world.para()
    closing_change(world, hero, guide, success)

    world.facts["outcome"] = "crossed" if success else "retreated"
    world.facts["success"] = success
    return world


PLACES = {
    "pine_trail": Place(
        id="pine_trail",
        label="the Pine Trail",
        opening="a pine trail where needles made the ground smell cool and green",
        goal="the little ranger tower",
        goal_image="From there, the pines looked like a folded green sea under the evening sky.",
        affords={"echo_tunnel", "rope_bridge"},
        tags={"trail", "tower"},
    ),
    "sea_cliffs": Place(
        id="sea_cliffs",
        label="the Sea Cliffs",
        opening="a cliff path above a bright, windy shore",
        goal="the shell lookout",
        goal_image="From there, the waves flashed silver and white far below.",
        affords={"rope_bridge", "cold_stream"},
        tags={"cliffs", "lookout"},
    ),
    "red_canyon": Place(
        id="red_canyon",
        label="the Red Canyon",
        opening="a red canyon path where the walls glowed warm as bread crust",
        goal="the high stone arch",
        goal_image="From there, the canyon shadows stretched long and purple over the sand.",
        affords={"echo_tunnel", "cold_stream"},
        tags={"canyon", "arch"},
    ),
}

OBSTACLES = {
    "rope_bridge": Obstacle(
        id="rope_bridge",
        label="a rope bridge",
        sight="The boards knocked softly under the wind, and the river below flashed between the gaps.",
        fear_need=4,
        crossing="the swaying bridge plank by plank",
        safe_alt="the longer meadow path",
        tags={"bridge", "river"},
    ),
    "echo_tunnel": Obstacle(
        id="echo_tunnel",
        label="an echo tunnel",
        sight="The tunnel mouth looked small and black, and every pebble sound came back twice.",
        fear_need=3,
        crossing="the tunnel by the wall-markers",
        safe_alt="the sunny ridge path",
        tags={"tunnel", "dark"},
    ),
    "cold_stream": Obstacle(
        id="cold_stream",
        label="a cold stream crossing",
        sight="The water hurried over the rocks, clear and quick, with white froth around the edges.",
        fear_need=5,
        crossing="the stream from stone to stone",
        safe_alt="the bend through the reeds",
        tags={"stream", "stones"},
    ),
}

GUIDES = {
    "hand_rope": Guide(
        id="hand_rope",
        label="the guide rope",
        phrase="Hold, look, step.",
        supports={"rope_bridge"},
        accuracy=3,
        courage_bonus=1,
        method="keep one hand on the rope, eyes on the next board, and feet slow",
        tags={"rope", "bridge"},
    ),
    "lantern_marks": Guide(
        id="lantern_marks",
        label="the little lantern and chalk marks",
        phrase="Shine, tap, step.",
        supports={"echo_tunnel"},
        accuracy=3,
        courage_bonus=1,
        method="shine the lantern low and tap each chalk mark before the next step",
        tags={"lantern", "dark"},
    ),
    "stone_count": Guide(
        id="stone_count",
        label="the counting map",
        phrase="One stone, next stone, steady feet.",
        supports={"cold_stream"},
        accuracy=3,
        courage_bonus=1,
        method="match the map to the stones and move in the counted order",
        tags={"map", "counting"},
    ),
    "guessing": Guide(
        id="guessing",
        label="a guessed path",
        phrase="Maybe this way.",
        supports=set(),
        accuracy=1,
        courage_bonus=0,
        method="just hurry and hope",
        tags={"guess"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Ava", "Nora", "Zoe", "Ivy", "Tess", "Ruby"]
BOY_NAMES = ["Finn", "Leo", "Max", "Eli", "Theo", "Sam", "Noah", "Jude"]
PRIZES = [
    "a brass lookout bell",
    "a bright shell tucked in the railing",
    "a red ribbon left by earlier hikers",
    "a smooth star-shaped stone",
]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    guide: str
    repeats: int = 3
    hero_name: str = "Mira"
    hero_gender: str = "girl"
    friend_name: str = "Finn"
    friend_gender: str = "boy"
    prize: str = "a brass lookout bell"
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


def pair_pick(rng: random.Random) -> tuple[str, str, str, str]:
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
    friend_name = rng.choice([n for n in pool if n != hero_name] or pool)
    return hero_name, hero_gender, friend_name, friend_gender


KNOWLEDGE = {
    "bridge": [
        (
            "Why do people hold a rope on a rope bridge?",
            "Holding the rope helps your body stay balanced when the bridge moves. A steady hand can make each step safer."
        )
    ],
    "dark": [
        (
            "Why do tunnels sound echoey?",
            "An echo happens when sound bounces off the hard walls and comes back to your ears. That is why even a tiny pebble tap can sound bigger in a tunnel."
        )
    ],
    "stream": [
        (
            "Why is it hard to cross a stream on stones?",
            "The stones can be wet and slippery, and the water keeps moving around them. Careful steps matter because rushing makes slipping easier."
        )
    ],
    "map": [
        (
            "What does an accurate map do?",
            "An accurate map shows where things really are. That helps people choose the right path instead of guessing."
        )
    ],
    "counting": [
        (
            "Why can counting help on a hard path?",
            "Counting gives your mind a simple pattern to follow. A pattern can make careful movement easier when you feel nervous."
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern helps you see where to put your feet in a dark place. Good light makes careful choices easier."
        )
    ],
    "rope": [
        (
            "Why can repeating words help when you feel afraid?",
            "Repeating calm words can slow your breathing and keep your mind on the next small step. That can make bravery feel possible."
        )
    ],
}
KNOWLEDGE_ORDER = ["bridge", "dark", "stream", "map", "counting", "lantern", "rope"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    obstacle = f["obstacle_cfg"]
    guide = f["guide_cfg"]
    place = f["place"]
    if f["outcome"] == "crossed":
        return [
            f'Write a short adventure story for a 3-to-5-year-old that includes the word "accurate" and a repeated guiding phrase.',
            f"Tell an adventure where {hero.label} feels afraid at {obstacle.label}, but {friend.label} uses {guide.label} and repetition to help {hero.pronoun('object')} grow brave.",
            f"Write a simple trail adventure set on {place.label} where accurate directions and repeated words help children make it through a hard place."
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "accurate" and a repeated guiding phrase.',
        f"Tell an adventure where {hero.label} and {friend.label} face {obstacle.label}, use accurate guidance, and learn that bravery can also mean turning back safely.",
        f"Write a gentle adventure about children on {place.label} who repeat a guiding phrase and choose the safe path when the hard way is still too big."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    obstacle = f["obstacle_cfg"]
    guide = f["guide_cfg"]
    place = f["place"]
    repeats = f["repeats"]
    prize = f["prize"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label} on a small trail adventure. They were trying to reach {place.goal} together."
        ),
        (
            f"What scared {hero.label}?",
            f"{obstacle.label.capitalize()} scared {hero.label}. The hard part was not just the place itself, but how big it suddenly felt when it was time to step forward."
        ),
        (
            f"How did {friend.label} try to help?",
            f"{friend.label} used {guide.label} and repeated the phrase '{guide.phrase}' {repeats} time{'s' if repeats != 1 else ''}. {friend.pronoun().capitalize()} wanted the plan to feel accurate and steady instead of rushed."
        ),
    ]
    if f["outcome"] == "crossed":
        qa.append(
            (
                f"Why was repeating the phrase important?",
                f"Each repetition raised {hero.label}'s courage and made the path feel clearer. Because the guide fit the obstacle, the repeated words turned fear into a step-by-step plan."
            )
        )
        qa.append(
            (
                "What happened at the end?",
                f"{hero.label} crossed safely, and the children reached {place.goal}. There they found {prize}, which showed that the adventure had truly opened up."
            )
        )
    else:
        qa.append(
            (
                "Did the children fail?",
                f"No. They did not cross the obstacle, but they still made a brave choice. They used accurate guidance, saw that the hard way was still too much, and chose the safer path instead."
            )
        )
        qa.append(
            (
                "What did they learn?",
                f"They learned that bravery is not the same as rushing. Sometimes the bravest ending is to turn back, keep the lesson, and come again another day."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    guide = world.facts["guide_cfg"]
    obstacle = world.facts["obstacle_cfg"]
    tags = set(guide.tags) | set(obstacle.tags)
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
        attrs = {k: v for k, v in ent.attrs.items() if v or isinstance(v, int)}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  repeats: {world.facts.get('repeats', 0)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pine_trail",
        obstacle="echo_tunnel",
        guide="lantern_marks",
        repeats=3,
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        prize="a brass lookout bell",
    ),
    StoryParams(
        place="sea_cliffs",
        obstacle="rope_bridge",
        guide="hand_rope",
        repeats=3,
        hero_name="Leo",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        prize="a bright shell tucked in the railing",
    ),
    StoryParams(
        place="red_canyon",
        obstacle="cold_stream",
        guide="stone_count",
        repeats=3,
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        prize="a smooth star-shaped stone",
    ),
    StoryParams(
        place="sea_cliffs",
        obstacle="cold_stream",
        guide="stone_count",
        repeats=2,
        hero_name="Ava",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        prize="a red ribbon left by earlier hikers",
    ),
]


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    guide = GUIDES[params.guide]
    return "crossed" if success_possible(obstacle, guide, params.repeats) else "retreated"


ASP_RULES = r"""
usable_guide(G, O) :- guide(G), obstacle(O), supports(G, O), accuracy(G, A), accuracy_min(M), A >= M.
valid(P, O, G) :- place(P), affords(P, O), usable_guide(G, O).

enough_courage :- chosen_obstacle(O), chosen_guide(G), repeats(R),
                  courage_bonus(G, B), fear_need(O, N), R + B >= N.
outcome(crossed) :- chosen_obstacle(O), chosen_guide(G), usable_guide(G, O), enough_courage.
outcome(retreated) :- chosen_obstacle(O), chosen_guide(G), usable_guide(G, O), not enough_courage.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for oid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, oid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("fear_need", oid, obstacle.fear_need))
    for gid, guide in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("accuracy", gid, guide.accuracy))
        lines.append(asp.fact("courage_bonus", gid, guide.courage_bonus))
        for oid in sorted(guide.supports):
            lines.append(asp.fact("supports", gid, oid))
    lines.append(asp.fact("accuracy_min", ACCURACY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_guide", params.guide),
            asp.fact("repeats", params.repeats),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: an adventure trail where accurate repeated guidance helps bravery grow."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--repeats", type=int, choices=[1, 2, 3], help="how many times the guiding phrase is repeated")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    obstacle = OBSTACLES.get(args.obstacle) if args.obstacle else None
    guide = GUIDES.get(args.guide) if args.guide else None

    if guide is not None and guide.accuracy < ACCURACY_MIN:
        raise StoryError(explain_rejection(place, obstacle, guide))
    if place is not None and obstacle is not None and obstacle.id not in place.affords:
        raise StoryError(explain_rejection(place, obstacle, guide))
    if obstacle is not None and guide is not None and not usable_guide(guide, obstacle):
        raise StoryError(explain_rejection(place, obstacle, guide))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.guide is None or combo[2] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, guide_id = rng.choice(combos)
    hero_name, hero_gender, friend_name, friend_gender = pair_pick(rng)

    if args.hero_gender:
        hero_gender = args.hero_gender
        hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elif args.hero_name:
        hero_name = args.hero_name

    if args.friend_gender:
        friend_gender = args.friend_gender
        pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
        friend_name = args.friend_name or rng.choice([n for n in pool if n != hero_name] or pool)
    elif args.friend_name:
        friend_name = args.friend_name

    if friend_name == hero_name:
        pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
        alts = [n for n in pool if n != hero_name]
        if not alts:
            raise StoryError("(No story: hero and friend cannot have the same name here.)")
        friend_name = rng.choice(alts)

    repeats = args.repeats if args.repeats is not None else rng.choice([2, 3, 3, 1])
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        guide=guide_id,
        repeats=repeats,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        prize=rng.choice(PRIZES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")
    if params.repeats not in {1, 2, 3}:
        raise StoryError("(Repeats must be 1, 2, or 3.)")

    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    guide = GUIDES[params.guide]

    if obstacle.id not in place.affords or not usable_guide(guide, obstacle):
        raise StoryError(explain_rejection(place, obstacle, guide))

    world = tell(
        place=place,
        obstacle=obstacle,
        guide=guide,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        repeats=params.repeats,
        prize=params.prize,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, guide) combos:\n")
        for place, obstacle, guide in combos:
            print(f"  {place:11} {obstacle:12} {guide}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} at {p.place}: {p.obstacle} with {p.guide} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
