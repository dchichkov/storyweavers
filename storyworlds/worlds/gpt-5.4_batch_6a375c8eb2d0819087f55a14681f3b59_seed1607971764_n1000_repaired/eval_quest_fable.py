#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/eval_quest_fable.py
==============================================

A standalone storyworld for a TinyStories-style fable about a small forest quest.

Seed:
    Words: eval
    Features: Quest
    Style: Fable

World premise
-------------
In a little forest, an elder sends a young animal on a quest to bring back
something the village needs before evening. Before any quest, the elder makes a
tiny "eval" -- a simple check of the path, the obstacle, and the right tool.
The story turns on whether the chosen preparation actually fits the obstacle.
When it does, the quest succeeds and the hero returns changed: less proud, more
wise.

The world uses one core reasonableness rule:
    an obstacle is only a good story if the chosen tool truly fits it

Examples:
    python storyworlds/worlds/gpt-5.4/eval_quest_fable.py
    python storyworlds/worlds/gpt-5.4/eval_quest_fable.py --obstacle river --tool raft
    python storyworlds/worlds/gpt-5.4/eval_quest_fable.py --obstacle river --tool lantern
    python storyworlds/worlds/gpt-5.4/eval_quest_fable.py --all
    python storyworlds/worlds/gpt-5.4/eval_quest_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/eval_quest_fable.py --verify
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
        female = {"hen", "doe", "mother", "woman"}
        male = {"fox", "badger", "father", "man"}
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
class HeroKind:
    id: str
    type: str
    title: str
    stride: str
    home_sound: str
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
class Need:
    id: str
    village_need: str
    request: str
    return_image: str
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
class Destination:
    id: str
    place: str
    image: str
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
    block_text: str
    danger_text: str
    lesson: str
    requires: str
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
class Tool:
    id: str
    label: str
    phrase: str
    use_text: str
    solves: set[str] = field(default_factory=set)
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
class ElderKind:
    id: str
    type: str
    title: str
    counsel: str
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


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    if hero.meters["attempting"] < THRESHOLD:
        return out
    sig = ("progress", obstacle.id, tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if tool.attrs.get("fits"):
        hero.meters["across"] += 1
        hero.meters["distance"] += 1
        hero.memes["confidence"] += 1
        out.append("__passed__")
    else:
        hero.meters["stuck"] += 1
        hero.meters["distance"] -= 1
        hero.memes["fear"] += 1
        hero.memes["humility"] += 1
        out.append("__stuck__")
    return out


def _r_return(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["distance"] < 2:
        return out
    sig = ("return", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["home_again"] += 1
    hero.memes["gratitude"] += 1
    out.append("__home__")
    return out


CAUSAL_RULES = [
    Rule(name="progress", tag="physical", apply=_r_progress),
    Rule(name="return", tag="physical", apply=_r_return),
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


def tool_fits(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.requires in tool.solves


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for hero_id in HEROES:
        for need_id in NEEDS:
            for dest_id in DESTINATIONS:
                for obs_id, obstacle in OBSTACLES.items():
                    for tool_id, tool in TOOLS.items():
                        if tool_fits(obstacle, tool):
                            combos.append((hero_id, need_id, dest_id, obs_id, tool_id))
    return combos


def explain_rejection(obstacle: Obstacle, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} does not honestly solve {obstacle.label}. "
        f"This quest world only tells stories where the elder's eval chooses a tool "
        f"that truly fits the obstacle.)"
    )


def predict_attempt(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["attempting"] += 1
    propagate(sim, narrate=False)
    return {
        "passed": hero.meters["across"] >= THRESHOLD,
        "stuck": hero.meters["stuck"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, hero_cfg: HeroKind, elder: Entity, elder_cfg: ElderKind) -> None:
    hero.memes["duty"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"In a small forest where even the stones seemed to listen, there lived "
        f"a young {hero_cfg.type} named {hero.id}. {hero_cfg.title} loved to "
        f"{hero_cfg.stride}, and at dusk {hero_cfg.home_sound}."
    )
    world.say(
        f"Over the village watched {elder_cfg.title}, an old {elder_cfg.type} who "
        f"always spoke softly and saw far."
    )


def call_quest(world: World, hero: Entity, need: Need, dest: Destination) -> None:
    world.say(
        f"One evening, the village had a need: {need.village_need}. "
        f"{hero.id} was asked to go to {dest.place} and bring back {need.request}."
    )
    world.say(
        f"Because it was a true quest and not a game, every step would matter."
    )


def elder_eval(world: World, elder: Entity, elder_cfg: ElderKind, obstacle: Obstacle, tool: Tool) -> None:
    world.facts["eval_word"] = "eval"
    tool_ent = world.get("tool")
    tool_ent.attrs["fits"] = tool_fits(OBSTACLES[world.facts["obstacle_cfg"].id], TOOLS[world.facts["tool_cfg"].id])
    pred = predict_attempt(world)
    world.facts["predicted_passed"] = pred["passed"]
    world.facts["predicted_stuck"] = pred["stuck"]
    world.say(
        f'Before {elder.pronoun("subject")} sent anyone out, {elder_cfg.title} made '
        f'a tiny eval. "{obstacle.block_text}," {elder.pronoun("subject")} said. '
        f'"So take {tool.phrase}. {elder_cfg.counsel}"'
    )


def boast(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'{hero.id} lifted {hero.pronoun("possessive")} chin. "I am small," '
        f'{hero.pronoun("subject")} said, "but I can be brave."'
    )


def set_out(world: World, hero: Entity, dest: Destination, obstacle: Obstacle) -> None:
    hero.meters["distance"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"So {hero.id} set out toward {dest.place}. {dest.image}."
    )
    world.say(
        f"Before long, {hero.pronoun('subject')} reached {obstacle.label}, and "
        f"{obstacle.danger_text}."
    )


def attempt(world: World, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    hero.meters["attempting"] += 1
    propagate(world, narrate=False)
    if hero.meters["across"] >= THRESHOLD:
        world.say(
            f"{hero.id} remembered the elder's eval and used {tool.phrase}. "
            f"{tool.use_text}."
        )
    else:
        world.say(
            f"{hero.id} tried to go on, but without the right help, {obstacle.label} "
            f"held {hero.pronoun('object')} fast."
        )


def turn(world: World, hero: Entity, elder_cfg: ElderKind, obstacle: Obstacle, tool: Tool) -> None:
    if hero.meters["across"] >= THRESHOLD:
        hero.memes["wisdom"] += 1
        world.say(
            f"Then {hero.id} understood that bravery is brightest when it listens. "
            f"The quest moved forward because {hero.pronoun('subject')} trusted the "
            f"careful eval instead of pride alone."
        )
    else:
        hero.memes["wisdom"] += 1
        world.say(
            f"For a moment, {hero.id} felt very small. Then {hero.pronoun('subject')} "
            f"remembered {elder_cfg.title}'s words, went back for {tool.phrase}, and "
            f"returned with a steadier heart."
        )
        hero.meters["attempting"] += 1
        world.get("tool").attrs["fits"] = True
        propagate(world, narrate=False)
        world.say(f"{tool.use_text}. This time, the way opened.")


def gather(world: World, hero: Entity, need: Need, dest: Destination) -> None:
    hero.meters["distance"] += 1
    hero.meters["carrying_need"] += 1
    world.say(
        f"At {dest.place}, {hero.id} found {need.request} and carried it home with "
        f"great care."
    )


def return_home(world: World, hero: Entity, need: Need, elder_cfg: ElderKind) -> None:
    propagate(world, narrate=False)
    world.say(
        f"When {hero.id} came back, {need.return_image}. The elder smiled, for the "
        f"quest had brought home more than a thing."
    )
    world.say(
        f"From that day on, {hero.id} was still brave, but no longer hasty. "
        f"{hero.pronoun('subject').capitalize()} would pause, make a small eval, "
        f"and choose the fitting way before taking the first step."
    )


def tell(
    hero_cfg: HeroKind,
    need: Need,
    dest: Destination,
    obstacle: Obstacle,
    tool: Tool,
    elder_cfg: ElderKind,
    hero_name: str = "Pip",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg.type, role="hero", label=hero_name))
    elder = world.add(Entity(id="elder", kind="character", type=elder_cfg.type, role="elder", label=elder_cfg.title))
    world.add(Entity(id="obstacle", kind="thing", type="obstacle", role="obstacle", label=obstacle.label))
    world.add(Entity(id="tool", kind="thing", type="tool", role="tool", label=tool.label, attrs={"fits": False}))
    world.facts.update(
        hero=hero,
        elder=elder,
        hero_cfg=hero_cfg,
        need_cfg=need,
        destination_cfg=dest,
        obstacle_cfg=obstacle,
        tool_cfg=tool,
        elder_cfg=elder_cfg,
        hero_name=hero_name,
    )

    introduce(world, hero, hero_cfg, elder, elder_cfg)
    call_quest(world, hero, need, dest)

    world.para()
    elder_eval(world, elder, elder_cfg, obstacle, tool)
    boast(world, hero)
    set_out(world, hero, dest, obstacle)

    world.para()
    attempt(world, hero, obstacle, tool)
    turn(world, hero, elder_cfg, obstacle, tool)
    gather(world, hero, need, dest)

    world.para()
    return_home(world, hero, need, elder_cfg)

    world.facts.update(
        success=hero.meters["carrying_need"] >= THRESHOLD and hero.meters["home_again"] >= THRESHOLD,
        crossed=hero.meters["across"] >= THRESHOLD,
        stumbled=hero.meters["stuck"] >= THRESHOLD,
        learned=hero.memes["wisdom"] >= THRESHOLD,
    )
    return world


HEROES = {
    "mouse": HeroKind(
        id="mouse",
        type="mouse",
        title="Pip the field mouse",
        stride="dart along root paths as if they were roads",
        home_sound="the crickets sang over the burrow doors",
        tags={"mouse", "forest"},
    ),
    "fox": HeroKind(
        id="fox",
        type="fox",
        title="Rill the young fox",
        stride="trot the fern paths with bright eyes",
        home_sound="the wind hummed in the briars",
        tags={"fox", "forest"},
    ),
    "badger": HeroKind(
        id="badger",
        type="badger",
        title="Moss the young badger",
        stride="pad down shaded lanes under the pines",
        home_sound="the beetles clicked under fallen bark",
        tags={"badger", "forest"},
    ),
}

NEEDS = {
    "moonseed": Need(
        id="moonseed",
        village_need="the lantern by the common had gone dim",
        request="a pinch of moonseed",
        return_image="the lantern glowed bright again and warm light lay across the square",
        tags={"light", "seed"},
    ),
    "mintleaf": Need(
        id="mintleaf",
        village_need="the soup pot needed one last fresh smell",
        request="a bundle of mintleaf",
        return_image="the soup steamed sweetly and every nose in the village lifted",
        tags={"food", "herb"},
    ),
    "silver_bell": Need(
        id="silver_bell",
        village_need="the morning gate bell had cracked and gone quiet",
        request="the little silver bell from the hill shrine",
        return_image="a clear bell note skipped through the trees and called everyone smiling to the gate",
        tags={"bell", "village"},
    ),
}

DESTINATIONS = {
    "hill_shrine": Destination(
        id="hill_shrine",
        place="the hill shrine",
        image="The path climbed between mossy stones and old thyme",
        tags={"hill"},
    ),
    "glade": Destination(
        id="glade",
        place="the moonlit glade",
        image="The path slipped under hazel branches until the leaves opened like a green curtain",
        tags={"glade"},
    ),
    "spring": Destination(
        id="spring",
        place="the fern spring",
        image="The path curled beside damp roots where the air tasted cool and green",
        tags={"spring"},
    ),
}

OBSTACLES = {
    "river": Obstacle(
        id="river",
        label="the quick river",
        block_text="A quick river bars the way",
        danger_text="the water hurried over stones and would sweep tiny feet aside",
        lesson="swift water asks for floating help",
        requires="float",
        tags={"river", "water"},
    ),
    "brambles": Obstacle(
        id="brambles",
        label="the thorny brambles",
        block_text="A thorny wall of brambles twists across the path",
        danger_text="the hooked thorns snatched at fur and made every careless step sting",
        lesson="thorns ask for guarding hands",
        requires="guard",
        tags={"brambles", "thorns"},
    ),
    "cave": Obstacle(
        id="cave",
        label="the dark cave-mouth",
        block_text="A dark cave-mouth swallows the path",
        danger_text="the shadows hid the floor, and one wrong step could turn an ankle on cold stone",
        lesson="darkness asks for clear light",
        requires="light",
        tags={"cave", "dark"},
    ),
}

TOOLS = {
    "raft": Tool(
        id="raft",
        label="raft",
        phrase="a little bark raft",
        use_text="With the bark raft under paw, the crossing bobbed and steadied, and the current carried nothing away",
        solves={"float"},
        tags={"raft", "water"},
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="a pair of thick leaf-gloves",
        use_text="The leaf-gloves took the scratches, and the thorns parted enough for a careful body to slip through",
        solves={"guard"},
        tags={"gloves", "thorns"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a firefly lantern",
        use_text="The lantern cast a patient pool of gold, and each safe stone showed its face before the next step",
        solves={"light"},
        tags={"lantern", "dark"},
    ),
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a coil of grass rope",
        use_text="The grass rope gave a steady hold where the bank was loose and muddy",
        solves=set(),
        tags={"rope"},
    ),
}

ELDERS = {
    "owl": ElderKind(
        id="owl",
        type="owl",
        title="Old Owl",
        counsel="Even a brave heart should travel with a wise paw",
        tags={"owl", "wisdom"},
    ),
    "tortoise": ElderKind(
        id="tortoise",
        type="tortoise",
        title="Grand Tortoise",
        counsel="A slow thought before the road is better than a fast regret on it",
        tags={"tortoise", "wisdom"},
    ),
}


@dataclass
class StoryParams:
    hero: str
    need: str
    destination: str
    obstacle: str
    tool: str
    elder: str
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
    "eval": [
        (
            "What is an eval in this story?",
            "Here, an eval is a simple check before starting. It means stopping to think about the problem and the tool that truly fits it.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a purpose. Someone travels to do an important job or bring something back.",
        )
    ],
    "river": [
        (
            "Why can a river be hard to cross?",
            "A river can push and pull with moving water. Small feet can slip on wet stones or be swept off balance.",
        )
    ],
    "brambles": [
        (
            "What are brambles?",
            "Brambles are thorny plants that grow in twisty tangles. Their hooks can scratch fur, skin, or clothes.",
        )
    ],
    "cave": [
        (
            "Why is a dark cave dangerous?",
            "In a dark cave, it is hard to see where to place your feet. Hidden rocks and holes can make you trip.",
        )
    ],
    "raft": [
        (
            "What does a raft do?",
            "A raft helps something float on water. It gives a safer way to cross than stepping straight into a fast current.",
        )
    ],
    "gloves": [
        (
            "Why do gloves help with thorns?",
            "Gloves cover your hands and take the scratches first. That lets you move brambles aside more safely.",
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern makes light so you can see where to step. Good light turns a hidden path into a clearer one.",
        )
    ],
    "fable": [
        (
            "What is a fable?",
            "A fable is a short story that teaches a lesson. Animals often act like people so the lesson is easy to remember.",
        )
    ],
}
KNOWLEDGE_ORDER = ["eval", "quest", "river", "brambles", "cave", "raft", "gloves", "lantern", "fable"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero_cfg = f["hero_cfg"]
    need = f["need_cfg"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    elder_cfg = f["elder_cfg"]
    return [
        (
            f'Write a short fable for a 3-to-5-year-old that includes the word "eval" '
            f'and follows a forest quest. A young {hero_cfg.type} must fetch {need.request} '
            f'and learns to trust a wise check before the journey.'
        ),
        (
            f"Tell a quest story where {f['hero_name']}, a young {hero_cfg.type}, meets "
            f"{obstacle.label} and succeeds because {elder_cfg.title} chose {tool.phrase} "
            f"during an eval."
        ),
        (
            f"Write a gentle fable about bravery and planning: the hero wants to act quickly, "
            f"but the right tool matters more than pride."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero_cfg = f["hero_cfg"]
    need = f["need_cfg"]
    dest = f["destination_cfg"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    elder_cfg = f["elder_cfg"]
    hero_name = f["hero_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a young {hero_cfg.type}, and {elder_cfg.title}, who sends {hero_name} on a quest. The village also matters because it is waiting for {need.request}.",
        ),
        (
            f"What was the quest?",
            f"{hero_name} had to go to {dest.place} and bring back {need.request}. It was important because {need.village_need}.",
        ),
        (
            "What was the eval?",
            f"The eval was the elder's careful check before the journey. {elder_cfg.title} looked at {obstacle.label} and chose {tool.phrase} because it truly matched the trouble on the path.",
        ),
    ]
    if f.get("stumbled"):
        qa.append(
            (
                f"Did {hero_name} have trouble on the way?",
                f"Yes. At first {hero_name} felt the obstacle stop the journey, and that made the lesson real. Then {hero_name} remembered the elder's words, used the right tool, and the path opened.",
            )
        )
    qa.append(
        (
            f"Why did {tool.label} help?",
            f"{tool.phrase.capitalize()} helped because {obstacle.lesson}. The fix worked for the exact danger instead of being only a random object to carry.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"{hero_name} came home with {need.request}, and {need.return_image}. The ending shows that the quest helped the village and made the hero wiser too.",
        )
    )
    qa.append(
        (
            "What lesson did the hero learn?",
            f"{hero_name} learned that bravery should listen to wisdom. The right eval and the fitting tool carried the quest farther than pride alone could.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"eval", "quest", "fable"}
    tags |= set(f["obstacle_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="mouse",
        need="moonseed",
        destination="glade",
        obstacle="river",
        tool="raft",
        elder="owl",
        hero_name="Pip",
    ),
    StoryParams(
        hero="fox",
        need="silver_bell",
        destination="hill_shrine",
        obstacle="cave",
        tool="lantern",
        elder="tortoise",
        hero_name="Rill",
    ),
    StoryParams(
        hero="badger",
        need="mintleaf",
        destination="spring",
        obstacle="brambles",
        tool="gloves",
        elder="owl",
        hero_name="Moss",
    ),
]


ASP_RULES = r"""
valid(H,N,D,O,T) :- hero(H), need(N), destination(D), obstacle(O), tool(T), requires(O,R), solves(T,R).

chosen_valid :- chosen_obstacle(O), chosen_tool(T), requires(O,R), solves(T,R).
outcome(success) :- chosen_valid.
outcome(invalid) :- not chosen_valid.

#show valid/5.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for did in DESTINATIONS:
        lines.append(asp.fact("destination", did))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("requires", oid, obstacle.requires))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for s in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, s))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        got = asp_outcome(params)
        want = "success"
        if got != want:
            rc = 1
            print(f"MISMATCH in outcome for {params}: asp={got} python={want}")

    try:
        smoke_params = CURATED[0]
        sample = generate(smoke_params)
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a forest quest fable with a small eval before the journey."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--hero-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid quest combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


NAME_BY_HERO = {
    "mouse": ["Pip", "Nip", "Mimi", "Tumble"],
    "fox": ["Rill", "Fern", "Ash", "Cinder"],
    "badger": ["Moss", "Bram", "Pebble", "Root"],
}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not tool_fits(obstacle, tool):
            raise StoryError(explain_rejection(obstacle, tool))

    combos = [
        c
        for c in valid_combos()
        if (args.hero is None or c[0] == args.hero)
        and (args.need is None or c[1] == args.need)
        and (args.destination is None or c[2] == args.destination)
        and (args.obstacle is None or c[3] == args.obstacle)
        and (args.tool is None or c[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero, need, destination, obstacle, tool = rng.choice(sorted(combos))
    elder = args.elder or rng.choice(sorted(ELDERS))
    hero_name = args.hero_name or rng.choice(NAME_BY_HERO[hero])
    return StoryParams(
        hero=hero,
        need=need,
        destination=destination,
        obstacle=obstacle,
        tool=tool,
        elder=elder,
        hero_name=hero_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"(Unknown hero '{params.hero}'.)")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need '{params.need}'.)")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination '{params.destination}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle '{params.obstacle}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool '{params.tool}'.)")
    if params.elder not in ELDERS:
        raise StoryError(f"(Unknown elder '{params.elder}'.)")

    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if not tool_fits(obstacle, tool):
        raise StoryError(explain_rejection(obstacle, tool))

    world = tell(
        hero_cfg=HEROES[params.hero],
        need=NEEDS[params.need],
        dest=DESTINATIONS[params.destination],
        obstacle=obstacle,
        tool=tool,
        elder_cfg=ELDERS[params.elder],
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, need, destination, obstacle, tool) combos:\n")
        for hero, need, destination, obstacle, tool in combos:
            print(f"  {hero:6} {need:11} {destination:11} {obstacle:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: quest for {p.need} via {p.obstacle} with {p.tool}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
