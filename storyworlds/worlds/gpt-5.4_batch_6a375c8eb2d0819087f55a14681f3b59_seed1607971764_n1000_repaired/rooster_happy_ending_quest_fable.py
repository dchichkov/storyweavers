#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rooster_happy_ending_quest_fable.py
==============================================================

A standalone storyworld for a small fable-like quest: a rooster leaves the farm
to fetch something needed by a friend, meets an obstacle on the path, and
succeeds only when he asks for help with humility.

The domain is deliberately small and constraint-checked:

* A quest needs a concrete goal item with a concrete recipient.
* The road to that item includes one obstacle.
* Only helpers with the right ability can honestly solve that obstacle.
* A humble rooster receives help and brings the item home.
* A boastful rooster is refused, and the quest fails.

Run it
------
    python storyworlds/worlds/gpt-5.4/rooster_happy_ending_quest_fable.py
    python storyworlds/worlds/gpt-5.4/rooster_happy_ending_quest_fable.py --goal clover --obstacle stream --helper duck
    python storyworlds/worlds/gpt-5.4/rooster_happy_ending_quest_fable.py --helper mouse
    python storyworlds/worlds/gpt-5.4/rooster_happy_ending_quest_fable.py --manner boastful
    python storyworlds/worlds/gpt-5.4/rooster_happy_ending_quest_fable.py --all
    python storyworlds/worlds/gpt-5.4/rooster_happy_ending_quest_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/rooster_happy_ending_quest_fable.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    abilities: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rooster"}:
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
class Goal:
    id: str
    item: str
    source: str
    recipient: str
    need: str
    use: str
    opening_image: str
    ending_image: str
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
    path_text: str
    danger_text: str
    needed_ability: str
    clear_text: str
    fail_text: str
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
class HelperCfg:
    id: str
    label: str
    type: str
    arrival_text: str
    method_text: str
    decline_text: str
    abilities: set[str] = field(default_factory=set)
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
class Manner:
    id: str
    ask_text: str
    thank_text: str
    humble: bool
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


def _r_stuck(world: World) -> list[str]:
    rooster = world.get("rooster")
    obstacle = world.get("obstacle")
    if rooster.meters["attempting"] < THRESHOLD:
        return []
    if obstacle.meters["blocking"] < THRESHOLD:
        return []
    if obstacle.meters["cleared"] >= THRESHOLD:
        return []
    sig = ("stuck", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rooster.meters["stuck"] += 1
    rooster.memes["worry"] += 1
    return []


def _r_cross(world: World) -> list[str]:
    rooster = world.get("rooster")
    obstacle = world.get("obstacle")
    if rooster.meters["attempting"] < THRESHOLD:
        return []
    if obstacle.meters["cleared"] < THRESHOLD:
        return []
    sig = ("cross", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rooster.meters["crossed"] += 1
    rooster.memes["hope"] += 1
    return []


def _r_deliver(world: World) -> list[str]:
    rooster = world.get("rooster")
    recipient = world.get("recipient")
    if rooster.meters["carrying"] < THRESHOLD:
        return []
    if rooster.meters["home"] < THRESHOLD:
        return []
    sig = ("deliver", recipient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    recipient.meters["helped"] += 1
    recipient.memes["relief"] += 1
    rooster.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck", tag="physical", apply=_r_stuck),
    Rule(name="cross", tag="physical", apply=_r_cross),
    Rule(name="deliver", tag="social", apply=_r_deliver),
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
        for line in produced:
            world.say(line)
    return produced


GOALS = {
    "clover": Goal(
        id="clover",
        item="a bundle of sweet clover",
        source="the far meadow",
        recipient="the little lamb",
        need="had pushed away breakfast after the hard night wind",
        use="one green mouthful might bring the lamb's appetite back",
        opening_image="The meadow beyond the farm shone pale and soft after the storm.",
        ending_image="The lamb nibbled the clover, then skipped in a small bright circle.",
        tags={"clover", "kindness"},
    ),
    "mint": Goal(
        id="mint",
        item="a cool sprig of mint",
        source="the brookside patch",
        recipient="the tired calf",
        need="had trudged in the heat and stood with drooping ears",
        use="the cool smell would cheer the calf and settle the long morning",
        opening_image="Down by the brook, mint leaves grew where the bank kept its shade.",
        ending_image="The calf sniffed the mint, snorted once, and began to prance again.",
        tags={"mint", "kindness"},
    ),
    "wheat": Goal(
        id="wheat",
        item="a bright ear of wheat",
        source="the old mill path",
        recipient="the hungry chicks",
        need="peeped in a worried cluster because the grain basket was nearly empty",
        use="even one good ear could be shared until the farmer filled the bin again",
        opening_image="Near the mill, late wheat bowed like little golden flags.",
        ending_image="The chicks pecked the grains one by one and soon their peeps sounded merry.",
        tags={"wheat", "kindness"},
    ),
}

OBSTACLES = {
    "stream": Obstacle(
        id="stream",
        label="the stream",
        path_text="a cold stream running across the path",
        danger_text="The stones in it shivered under the water, and the current tugged at every reed.",
        needed_ability="swim",
        clear_text="showed him the shallow stepping place and kept beside him until he crossed",
        fail_text="stared at the quick water until his proud feet felt very small",
        tags={"stream"},
    ),
    "hedge": Obstacle(
        id="hedge",
        label="the thorn hedge",
        path_text="a thorn hedge tangled over the path",
        danger_text="Its hooks caught at feathers and left no honest gap for a careful bird.",
        needed_ability="open_hedge",
        clear_text="made a safe opening through the thorny branches",
        fail_text="paced beside the hedge and found only more thorns and more thorns",
        tags={"hedge"},
    ),
    "stones": Obstacle(
        id="stones",
        label="the loose stones",
        path_text="a slope of loose stones under the hill",
        danger_text="Each pebble slipped when he set his claws upon it, and the whole path seemed to slide away.",
        needed_ability="steady_path",
        clear_text="tested the ground, chose the firm places, and led him up the slope",
        fail_text="scrabbled twice, slid back twice, and had to stop before he tumbled",
        tags={"stones"},
    ),
}

HELPERS = {
    "duck": HelperCfg(
        id="duck",
        label="the duck",
        type="duck",
        arrival_text="Just then the duck glided from the reeds and tipped a bright eye toward him.",
        method_text="The duck loves quiet water and knows where a stream is kind.",
        decline_text="The duck tucked one wing close and said, \"Water does not listen to bragging.\"",
        abilities={"swim"},
        tags={"duck"},
    ),
    "goat": HelperCfg(
        id="goat",
        label="the goat",
        type="goat",
        arrival_text="From the side field came the goat, nibbling as if every path in the world belonged to her.",
        method_text="The goat is sure-footed and fearless around thorn and stone.",
        decline_text="The goat gave a short snort and said, \"A stiff neck fits badly through a narrow path.\"",
        abilities={"open_hedge", "steady_path"},
        tags={"goat"},
    ),
    "dog": HelperCfg(
        id="dog",
        label="the old sheepdog",
        type="dog",
        arrival_text="Soon the old sheepdog padded over, slow and steady, with burrs in his tail.",
        method_text="The sheepdog has walked every lane and slope around the farm for years.",
        decline_text="The old sheepdog sat down and said, \"A loud chest does not make a safe road.\"",
        abilities={"steady_path"},
        tags={"dog"},
    ),
    "mouse": HelperCfg(
        id="mouse",
        label="the field mouse",
        type="mouse",
        arrival_text="A field mouse peeped from the grass, whiskers twitching like little threads.",
        method_text="The field mouse knows the small ways under leaf and branch.",
        decline_text="The mouse folded tiny paws and said, \"Big words do not widen small doors.\"",
        abilities={"open_hedge"},
        tags={"mouse"},
    ),
}

MANNERS = {
    "humble": Manner(
        id="humble",
        ask_text="\"Friend, I cannot finish this quest alone. Will you help me?\"",
        thank_text="\"Thank you,\" said the rooster. \"A good road is brighter when two hearts walk it.\"",
        humble=True,
        tags={"kindness", "asking_help"},
    ),
    "boastful": Manner(
        id="boastful",
        ask_text="\"Stand aside and watch,\" said the rooster. \"I need no one. I only asked so you could admire me.\"",
        thank_text="",
        humble=False,
        tags={"pride"},
    ),
}


def helper_can_clear(helper: HelperCfg, obstacle: Obstacle) -> bool:
    return obstacle.needed_ability in helper.abilities


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for goal_id in GOALS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for helper_id, helper in HELPERS.items():
                if helper_can_clear(helper, obstacle):
                    combos.append((goal_id, obstacle_id, helper_id))
    return combos


def predict_attempt(world: World) -> dict:
    sim = world.copy()
    rooster = sim.get("rooster")
    obstacle = sim.get("obstacle")
    rooster.meters["attempting"] = 1
    obstacle.meters["blocking"] = 1
    propagate(sim, narrate=False)
    return {
        "stuck": rooster.meters["stuck"] >= THRESHOLD,
        "worry": rooster.memes["worry"],
    }


def introduce(world: World, rooster: Entity, goal: Goal) -> None:
    rooster.memes["pride"] = 1
    world.say(
        f"At the edge of a small farm lived {rooster.id}, a rooster with a scarlet comb, a bright step, and a voice that liked the first word each morning."
    )
    world.say(goal.opening_image)
    world.say(
        f"That same dawn, {goal.recipient} {goal.need}, and everyone on the farm spoke in softer voices than usual."
    )


def need(world: World, rooster: Entity, goal: Goal) -> None:
    rooster.memes["care"] += 1
    world.say(
        f'"If only someone could bring back {goal.item} from {goal.source},\" said the old hen. \"They say {goal.use}.\"'
    )
    world.say(
        f'{rooster.id} lifted his head. "Then I will go," {rooster.pronoun()} said. A quest had opened before him, and he stepped into it at once.'
    )


def set_out(world: World, rooster: Entity, goal: Goal, obstacle: Obstacle) -> None:
    rooster.meters["distance"] += 1
    world.say(
        f"He set out toward {goal.source}. Before long he came to {obstacle.path_text}."
    )
    world.say(obstacle.danger_text)


def warn(world: World, rooster: Entity, obstacle: Obstacle) -> None:
    pred = predict_attempt(world)
    world.facts["predicted_stuck"] = pred["stuck"]
    if pred["stuck"]:
        world.say(
            f"{rooster.id} saw at once that brave feathers were not the same thing as a safe crossing."
        )


def ask_for_help(world: World, rooster: Entity, helper: Entity, helper_cfg: HelperCfg, manner: Manner) -> None:
    world.say(helper_cfg.arrival_text)
    world.say(helper_cfg.method_text)
    world.say(manner.ask_text)
    if manner.humble:
        rooster.memes["humility"] += 1
        helper.memes["trust"] += 1
    else:
        rooster.memes["pride"] += 1
        helper.memes["distance"] += 1


def refuse(world: World, rooster: Entity, helper_cfg: HelperCfg, obstacle: Obstacle) -> None:
    rooster.meters["attempting"] = 1
    world.get("obstacle").meters["blocking"] = 1
    propagate(world, narrate=False)
    world.say(helper_cfg.decline_text)
    world.say(
        f"{rooster.id} {obstacle.fail_text}. At last {rooster.pronoun()} turned back toward the yard with an empty beak and a heavy heart."
    )


def assist(world: World, rooster: Entity, helper: Entity, obstacle: Entity, helper_cfg: HelperCfg, obstacle_cfg: Obstacle) -> None:
    helper.meters["assisting"] = 1
    obstacle.meters["blocking"] = 1
    obstacle.meters["cleared"] = 1
    rooster.meters["attempting"] = 1
    propagate(world, narrate=False)
    world.say(
        f"{helper_cfg.label.capitalize()} {obstacle_cfg.clear_text}, and soon the rooster was over the trouble that had stopped him."
    )


def take_item(world: World, rooster: Entity, goal: Goal) -> None:
    rooster.meters["carrying"] = 1
    rooster.meters["distance"] += 1
    world.say(
        f"Beyond the obstacle lay {goal.source}, just as the old hen had said. There {rooster.id} found {goal.item} and lifted it carefully in {rooster.pronoun('possessive')} beak."
    )


def return_and_deliver(world: World, rooster: Entity, helper: Entity, goal: Goal, manner: Manner) -> None:
    rooster.meters["home"] = 1
    propagate(world, narrate=False)
    world.say(
        f"Back at the farm, {rooster.id} laid {goal.item} before {goal.recipient}."
    )
    if manner.humble:
        rooster.memes["gratitude"] += 1
        helper.memes["warmth"] += 1
        world.say(manner.thank_text)
    world.say(goal.ending_image)
    world.say(
        f"And from that day on, when the rooster sang at dawn, the sound carried not only pride, but kindness as well."
    )


def lesson_after_failure(world: World, rooster: Entity, helper_cfg: HelperCfg) -> None:
    rooster.memes["humility"] += 1
    world.say(
        f"All that evening {rooster.id} remembered {helper_cfg.label}'s answer. Pride had made {rooster.pronoun('object')} loud, but it had not made {rooster.pronoun('object')} useful."
    )
    world.say(
        "So the next morning, before the sun touched the fence, he promised himself that on the next hard road he would ask more gently."
    )


def tell(
    goal: Goal,
    obstacle_cfg: Obstacle,
    helper_cfg: HelperCfg,
    manner: Manner,
    rooster_name: str = "Rufus",
) -> World:
    world = World()
    rooster = world.add(Entity(id="rooster", kind="character", type="rooster", label=rooster_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, label=helper_cfg.label, role="helper", abilities=set(helper_cfg.abilities)))
    obstacle = world.add(Entity(id="obstacle", kind="thing", type="obstacle", label=obstacle_cfg.label, role="obstacle"))
    recipient = world.add(Entity(id="recipient", kind="character", type="animal", label=goal.recipient, role="recipient"))

    rooster.attrs["display_name"] = rooster_name
    helper.attrs["cfg"] = helper_cfg.id
    obstacle.attrs["cfg"] = obstacle_cfg.id
    recipient.attrs["goal"] = goal.id

    rooster.meters["attempting"] = 0
    rooster.meters["carrying"] = 0
    rooster.meters["home"] = 0
    rooster.meters["stuck"] = 0
    rooster.meters["crossed"] = 0
    helper.meters["assisting"] = 0
    obstacle.meters["blocking"] = 0
    obstacle.meters["cleared"] = 0
    recipient.meters["helped"] = 0
    recipient.memes["relief"] = 0
    world.facts["predicted_stuck"] = False

    introduce(world, rooster, goal)
    need(world, rooster, goal)

    world.para()
    set_out(world, rooster, goal, obstacle_cfg)
    warn(world, rooster, obstacle_cfg)
    ask_for_help(world, rooster, helper, helper_cfg, manner)

    if manner.humble:
        world.para()
        assist(world, rooster, helper, obstacle, helper_cfg, obstacle_cfg)
        take_item(world, rooster, goal)
        world.para()
        return_and_deliver(world, rooster, helper, goal, manner)
        outcome = "success"
    else:
        world.para()
        refuse(world, rooster, helper_cfg, obstacle_cfg)
        lesson_after_failure(world, rooster, helper_cfg)
        outcome = "failed"

    world.facts.update(
        rooster=rooster,
        rooster_name=rooster_name,
        helper=helper,
        helper_cfg=helper_cfg,
        obstacle=obstacle,
        obstacle_cfg=obstacle_cfg,
        recipient=recipient,
        goal=goal,
        manner=manner,
        outcome=outcome,
        helped=recipient.meters["helped"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    goal: str
    obstacle: str
    helper: str
    manner: str
    rooster_name: str
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
    "rooster": [
        (
            "What is a rooster?",
            "A rooster is an adult male chicken. Many roosters are known for crowing at dawn.",
        )
    ],
    "duck": [
        (
            "Why is a duck good near water?",
            "A duck has webbed feet and a body made for floating and paddling. That helps it move calmly through water where other animals may slip.",
        )
    ],
    "goat": [
        (
            "Why can a goat help on rough ground?",
            "Goats are good climbers and can keep their balance on uneven places. They are also bold around bushes and rocky paths.",
        )
    ],
    "dog": [
        (
            "Why might an old dog know the road well?",
            "An old farm dog has walked many paths again and again. Experience can make someone a wise guide.",
        )
    ],
    "mouse": [
        (
            "How can a small mouse help with a hedge?",
            "A mouse notices tiny gaps that bigger animals miss. Being small can be useful when a path is narrow.",
        )
    ],
    "stream": [
        (
            "Why can a stream be hard to cross?",
            "Running water can push against your feet, and slippery stones are hard to stand on. Even a small stream may be tricky if you rush.",
        )
    ],
    "hedge": [
        (
            "Why is a thorn hedge dangerous?",
            "A thorn hedge has sharp points that can scratch skin or catch feathers. It is safer to find a proper opening than to force your way through.",
        )
    ],
    "stones": [
        (
            "Why are loose stones hard to walk on?",
            "Loose stones roll and slide when you step on them. That makes it easy to lose your balance.",
        )
    ],
    "clover": [
        (
            "What is clover?",
            "Clover is a small green plant with soft leaves. Many grazing animals like to nibble it.",
        )
    ],
    "mint": [
        (
            "What is mint?",
            "Mint is a plant with cool-smelling leaves. People and animals notice its fresh scent right away.",
        )
    ],
    "wheat": [
        (
            "What is wheat?",
            "Wheat is a grain plant that grows in tall stalks. Its seeds can be ground into flour or pecked as food.",
        )
    ],
    "kindness": [
        (
            "Why is kindness useful on a quest?",
            "Kindness helps others feel safe enough to help you. A gentle voice can open a path that pride leaves closed.",
        )
    ],
    "asking_help": [
        (
            "Is asking for help a weak thing to do?",
            "No. Asking for help can be wise and brave when a job is too hard to do alone.",
        )
    ],
    "pride": [
        (
            "Why can pride cause trouble?",
            "Pride can make someone ignore good advice. When pride grows too big, it may block learning and friendship.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "rooster",
    "duck",
    "goat",
    "dog",
    "mouse",
    "stream",
    "hedge",
    "stones",
    "clover",
    "mint",
    "wheat",
    "kindness",
    "asking_help",
    "pride",
]


CURATED = [
    StoryParams(
        goal="clover",
        obstacle="stream",
        helper="duck",
        manner="humble",
        rooster_name="Rufus",
    ),
    StoryParams(
        goal="mint",
        obstacle="hedge",
        helper="goat",
        manner="humble",
        rooster_name="Bram",
    ),
    StoryParams(
        goal="wheat",
        obstacle="stones",
        helper="dog",
        manner="humble",
        rooster_name="Cinder",
    ),
    StoryParams(
        goal="clover",
        obstacle="hedge",
        helper="mouse",
        manner="boastful",
        rooster_name="Pip",
    ),
]


def explain_rejection(helper: HelperCfg, obstacle: Obstacle) -> str:
    needed = obstacle.needed_ability.replace("_", " ")
    has = ", ".join(sorted(a.replace("_", " ") for a in helper.abilities)) or "no matching skill"
    return (
        f"(No story: {helper.label} cannot honestly solve {obstacle.label}. "
        f"This obstacle needs a helper who can {needed}, but this helper offers {has}.)"
    )


def outcome_of(params: StoryParams) -> str:
    manner = MANNERS[params.manner]
    return "success" if manner.humble else "failed"


def generation_prompts(world: World) -> list[str]:
    goal = world.facts["goal"]
    rooster_name = world.facts["rooster_name"]
    helper_cfg = world.facts["helper_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "success":
        return [
            f'Write a short fable about a rooster who goes on a quest to bring back {goal.item}. Include the word "rooster".',
            f"Tell a child-friendly quest where {rooster_name} meets trouble on the road, asks {helper_cfg.label} for help, and comes home wiser.",
            "Write a simple fable with a happy ending that teaches that humility and kindness can carry a traveler farther than pride.",
        ]
    return [
        f'Write a short fable about a rooster who starts a quest for {goal.item} but lets pride spoil the journey. Include the word "rooster".',
        f"Tell a gentle cautionary tale where {rooster_name} meets trouble on the road and loses help by boasting to {helper_cfg.label}.",
        "Write a fable that shows how pride can close a door that kindness would have opened.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    goal = world.facts["goal"]
    helper_cfg = world.facts["helper_cfg"]
    obstacle_cfg = world.facts["obstacle_cfg"]
    rooster_name = world.facts["rooster_name"]
    manner = world.facts["manner"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {rooster_name}, a rooster who went on a quest, and {helper_cfg.label} who met him on the road.",
        ),
        (
            f"Why did {rooster_name} leave the farm?",
            f"He left to bring back {goal.item} from {goal.source} for {goal.recipient}. The quest mattered because {goal.recipient} needed comfort and the farm hoped that gift would help.",
        ),
        (
            f"What stopped {rooster_name} on the way?",
            f"He came to {obstacle_cfg.label}. It was dangerous because {obstacle_cfg.danger_text[0].lower() + obstacle_cfg.danger_text[1:]}",
        ),
    ]
    if outcome == "success":
        qa.append(
            (
                f"How did {helper_cfg.label} help the rooster?",
                f"{helper_cfg.label.capitalize()} {obstacle_cfg.clear_text}. That changed the path from something risky into something the rooster could safely cross.",
            )
        )
        qa.append(
            (
                f"Why did the quest end happily?",
                f"It ended happily because the rooster asked with humility and accepted help. After that, he could fetch {goal.item}, bring it home, and help {goal.recipient}.",
            )
        )
        qa.append(
            (
                "What lesson did the rooster learn?",
                f"He learned that pride alone is noisy, but kindness is useful. His song at the end showed that something inside him had changed as well as the world around him.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {helper_cfg.label} refuse to help?",
                f"{helper_cfg.label.capitalize()} refused because the rooster spoke with pride instead of humility. The hard road needed friendship and trust, and boasting pushed both of those away.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                "The rooster came back empty-beaked and sad, but wiser than before. He did not get the prize that day, yet he learned what kind of voice he should use on the next quest.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rooster"}
    tags |= set(world.facts["goal"].tags)
    tags |= set(world.facts["helper_cfg"].tags)
    tags |= set(world.facts["obstacle_cfg"].tags)
    tags |= set(world.facts["manner"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.abilities:
            bits.append(f"abilities={sorted(ent.abilities)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% compatibility
can_help(H, O) :- helper(H), obstacle(O), needs(O, A), has(H, A).
valid(G, O, H) :- goal(G), obstacle(O), helper(H), can_help(H, O).

% ending logic
success :- chosen_manner(humble), chosen_helper(H), chosen_obstacle(O), can_help(H, O).
failed  :- not success.

outcome(success) :- success.
outcome(failed)  :- failed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.needed_ability))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for ability in sorted(helper.abilities):
            lines.append(asp.fact("has", helper_id, ability))
    for manner_id in MANNERS:
        lines.append(asp.fact("manner", manner_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_goal", params.goal),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_manner", params.manner),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rooster's quest, an obstacle, and the help humility can win."
    )
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--manner", choices=MANNERS, help="how the rooster asks for help")
    ap.add_argument("--rooster-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible quest set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


ROOSTER_NAMES = ["Rufus", "Bram", "Pip", "Cinder", "Milo", "Scarlet", "Ash", "Copper"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.obstacle:
        helper = HELPERS[args.helper]
        obstacle = OBSTACLES[args.obstacle]
        if not helper_can_clear(helper, obstacle):
            raise StoryError(explain_rejection(helper, obstacle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.goal is None or combo[0] == args.goal)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    goal_id, obstacle_id, helper_id = rng.choice(sorted(combos))
    if args.manner is not None:
        manner = args.manner
    else:
        manner = rng.choices(["humble", "boastful"], weights=[5, 1], k=1)[0]
    rooster_name = args.rooster_name or rng.choice(ROOSTER_NAMES)
    return StoryParams(
        goal=goal_id,
        obstacle=obstacle_id,
        helper=helper_id,
        manner=manner,
        rooster_name=rooster_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.manner not in MANNERS:
        raise StoryError(f"(Unknown manner: {params.manner})")

    goal = GOALS[params.goal]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    manner = MANNERS[params.manner]

    if not helper_can_clear(helper, obstacle):
        raise StoryError(explain_rejection(helper, obstacle))

    world = tell(
        goal=goal,
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        manner=manner,
        rooster_name=params.rooster_name,
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
        print(f"{len(combos)} compatible (goal, obstacle, helper) combos:\n")
        for goal_id, obstacle_id, helper_id in combos:
            print(f"  {goal_id:7} {obstacle_id:7} {helper_id}")
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
            header = f"### {p.rooster_name}: {p.goal} via {p.obstacle} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
