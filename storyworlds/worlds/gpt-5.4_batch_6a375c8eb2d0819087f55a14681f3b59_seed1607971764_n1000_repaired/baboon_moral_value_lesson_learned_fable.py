#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/baboon_moral_value_lesson_learned_fable.py
=====================================================================

A small fable-style storyworld about a young baboon, a tempting shortcut, and a
wiser animal who offers help. The world models a concrete obstacle, a risky
shortcut, and a helper whose safer plan really fits the situation. The central
value is humility: some baboons listen at once, while others learn only after a
stumble.

Run it
------
    python storyworlds/worlds/gpt-5.4/baboon_moral_value_lesson_learned_fable.py
    python storyworlds/worlds/gpt-5.4/baboon_moral_value_lesson_learned_fable.py --obstacle creek --shortcut log --helper tortoise
    python storyworlds/worlds/gpt-5.4/baboon_moral_value_lesson_learned_fable.py --obstacle thorns --shortcut stones
    python storyworlds/worlds/gpt-5.4/baboon_moral_value_lesson_learned_fable.py --all
    python storyworlds/worlds/gpt-5.4/baboon_moral_value_lesson_learned_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/baboon_moral_value_lesson_learned_fable.py --trace
    python storyworlds/worlds/gpt-5.4/baboon_moral_value_lesson_learned_fable.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe"}
        male = {"boy", "father", "baboon", "tortoise", "hornbill", "elephant", "monkey"}
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
class Obstacle:
    id: str
    label: str
    phrase: str
    far_side: str
    hazard: int
    harm: str
    danger_line: str
    safe_line: str
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
class Shortcut:
    id: str
    label: str
    boast: str
    action: str
    fails: str
    works_for: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    type: str
    label: str
    title: str
    caution_style: str
    rescue_text: str
    wisdom: int
    supports: set[str] = field(default_factory=set)
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
class Fruit:
    id: str
    label: str
    tree: str
    scent: str
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


def _r_stumble(world: World) -> list[str]:
    baboon = world.get("baboon")
    obstacle = world.get("obstacle")
    shortcut = world.get("shortcut")
    if baboon.meters["attempting"] < THRESHOLD:
        return []
    sig = ("stumble",)
    if sig in world.fired:
        return []
    hazard = int(obstacle.attrs["hazard"])
    grip = int(shortcut.attrs["grip"])
    if hazard <= grip:
        return []
    world.fired.add(sig)
    baboon.meters["stumbled"] += 1
    baboon.meters[obstacle.attrs["harm"]] += 1
    baboon.memes["fear"] += 1
    baboon.memes["humility"] += 1
    baboon.memes["pride"] = max(0.0, baboon.memes["pride"] - 1.0)
    return ["__stumble__"]


def _r_concern(world: World) -> list[str]:
    baboon = world.get("baboon")
    helper = world.get("helper")
    if baboon.meters["stumbled"] < THRESHOLD:
        return []
    sig = ("concern",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["concern"] += 1
    return []


def _r_gratitude(world: World) -> list[str]:
    baboon = world.get("baboon")
    helper = world.get("helper")
    if baboon.meters["rescued"] < THRESHOLD:
        return []
    sig = ("gratitude",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    baboon.memes["gratitude"] += 1
    helper.memes["kindness"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stumble", tag="physical", apply=_r_stumble),
    Rule(name="concern", tag="social", apply=_r_concern),
    Rule(name="gratitude", tag="social", apply=_r_gratitude),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


OBSTACLES = {
    "creek": Obstacle(
        id="creek",
        label="creek",
        phrase="a quick creek glittered between him and the fruit tree",
        far_side="the other bank",
        hazard=3,
        harm="wet",
        danger_line="The stones in the creek looked round and slick.",
        safe_line="A slow, steady crossing would keep little feet from slipping.",
        tags={"creek", "water"},
    ),
    "thorns": Obstacle(
        id="thorns",
        label="thorn patch",
        phrase="a thorn patch bristled between him and the fruit tree",
        far_side="the sunny side beyond the thorns",
        hazard=3,
        harm="scratched",
        danger_line="The thorns were thin, sharp, and eager to catch fur.",
        safe_line="A careful path over the patch would keep sharp thorns away.",
        tags={"thorns", "careful"},
    ),
    "ditch": Obstacle(
        id="ditch",
        label="muddy ditch",
        phrase="a muddy ditch lay between him and the fruit tree",
        far_side="the firm grass on the far side",
        hazard=2,
        harm="muddy",
        danger_line="The ditch looked shallow, but its edges were greasy with mud.",
        safe_line="A balanced crossing would reach the far side without a slide.",
        tags={"ditch", "mud"},
    ),
}

SHORTCUTS = {
    "stones": Shortcut(
        id="stones",
        label="hopping stones",
        boast="I need no advice. I will fly across on the stones.",
        action="bounded onto the stones",
        fails="One stone rolled under his foot, and he splashed down with a startled yelp.",
        works_for={"creek", "ditch"},
        tags={"stones", "shortcut"},
    ),
    "log": Shortcut(
        id="log",
        label="a narrow log",
        boast="Watch me. I can race across that log faster than any warning.",
        action="ran along the narrow log",
        fails="The log wobbled, his arms windmilled, and down he tumbled in a most undignified heap.",
        works_for={"creek", "ditch"},
        tags={"log", "balance"},
    ),
    "jump": Shortcut(
        id="jump",
        label="one grand jump",
        boast="I need only one grand jump to show how clever I am.",
        action="sprang with all his might",
        fails="He did not land where he meant to, and the trouble met him before the fruit did.",
        works_for={"ditch", "thorns"},
        tags={"jump", "boast"},
    ),
}

HELPERS = {
    "tortoise": Helper(
        id="tortoise",
        type="tortoise",
        label="Old Tortoise",
        title="Old Tortoise",
        caution_style="Slow feet reach places that proud feet miss.",
        rescue_text="showed him the firm stepping places and waited while he crossed one careful step at a time",
        wisdom=3,
        supports={"creek", "ditch", "thorns"},
        tags={"tortoise", "patience"},
    ),
    "hornbill": Helper(
        id="hornbill",
        type="hornbill",
        label="Hornbill",
        title="Hornbill",
        caution_style="From above, I can see which way is safe.",
        rescue_text="flew ahead, called out the safest path, and guided him neatly to the far side",
        wisdom=2,
        supports={"creek", "thorns", "ditch"},
        tags={"hornbill", "guidance"},
    ),
    "elephant": Helper(
        id="elephant",
        type="elephant",
        label="Aunt Elephant",
        title="Aunt Elephant",
        caution_style="Strength is finest when it walks beside good sense.",
        rescue_text="laid a thick branch across the trouble and stood beside it until he crossed in safety",
        wisdom=3,
        supports={"creek", "ditch", "thorns"},
        tags={"elephant", "help"},
    ),
}

FRUITS = {
    "figs": Fruit(
        id="figs",
        label="figs",
        tree="a fig tree",
        scent="sweet figs warming in the sun",
        tags={"figs"},
    ),
    "mangoes": Fruit(
        id="mangoes",
        label="mangoes",
        tree="a mango tree",
        scent="ripe mangoes smelling of honey",
        tags={"mango"},
    ),
    "plums": Fruit(
        id="plums",
        label="plums",
        tree="a plum tree",
        scent="dark plums shining among the leaves",
        tags={"plum"},
    ),
}

BABOON_NAMES = ["Bobo", "Kito", "Mosi", "Tamu", "Rafi"]
TEMPERAMENTS = ["proud", "hasty", "thoughtful", "gentle"]


def shortcut_grip(shortcut_id: str) -> int:
    return {
        "stones": 1,
        "log": 1,
        "jump": 0,
    }[shortcut_id]


def helper_can_solve(helper: Helper, obstacle: Obstacle) -> bool:
    return obstacle.id in helper.supports


def shortcut_fits(shortcut: Shortcut, obstacle: Obstacle) -> bool:
    return obstacle.id in shortcut.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for obs_id, obstacle in OBSTACLES.items():
        for sc_id, shortcut in SHORTCUTS.items():
            if not shortcut_fits(shortcut, obstacle):
                continue
            for hp_id, helper in HELPERS.items():
                if helper_can_solve(helper, obstacle):
                    combos.append((obs_id, sc_id, hp_id))
    return combos


def listen_first(temperament: str, helper: Helper) -> bool:
    if temperament in {"thoughtful", "gentle"}:
        return True
    return helper.wisdom >= 4


def predict_attempt(obstacle: Obstacle, shortcut: Shortcut) -> dict:
    grip = shortcut_grip(shortcut.id)
    stumble = obstacle.hazard > grip
    return {
        "stumble": stumble,
        "harm": obstacle.harm if stumble else "",
    }


def introduce(world: World, baboon: Entity, fruit: Fruit, obstacle: Obstacle) -> None:
    baboon.memes["hunger"] += 1
    world.say(
        f"One bright morning, a young baboon named {baboon.id} climbed a low rock and sniffed the air. "
        f"Across the way stood {fruit.tree}, and {fruit.scent} made his mouth water."
    )
    world.say(
        f"But {obstacle.phrase}. {obstacle.danger_line}"
    )


def boast(world: World, baboon: Entity, shortcut: Shortcut) -> None:
    baboon.memes["pride"] += 1
    world.say(
        f'"{shortcut.boast}" said {baboon.id}, puffing out his chest.'
    )


def warning(world: World, helper: Entity, obstacle: Obstacle) -> None:
    world.say(
        f'{helper.label} was nearby and shook {helper.pronoun("possessive")} head. '
        f'"{helper.attrs["caution_style"]} {obstacle.safe_line}"'
    )


def choose_wisely(world: World, baboon: Entity, helper: Entity, fruit: Fruit, obstacle: Obstacle) -> None:
    baboon.memes["humility"] += 1
    baboon.memes["trust"] += 1
    baboon.meters["crossed"] += 1
    baboon.memes["joy"] += 1
    world.say(
        f"{baboon.id} looked again at the trouble before him. This time he saw that the danger was real, "
        f"not small."
    )
    world.say(
        f"He bowed his head a little and said, \"Please show me the safe way.\" "
        f"So {helper.label} {helper.attrs['rescue_text']}."
    )
    world.say(
        f"Soon the young baboon stood on {obstacle.far_side} with {fruit.label} in his hands, and they tasted sweeter "
        f"because he had earned them without foolishness."
    )


def defy(world: World, baboon: Entity, shortcut: Shortcut) -> None:
    baboon.meters["attempting"] += 1
    baboon.memes["defiance"] += 1
    world.say(
        f"But {baboon.id} was too full of himself to listen. He {shortcut.action}."
    )
    propagate(world, narrate=False)


def stumble_scene(world: World, baboon: Entity, shortcut: Shortcut, obstacle: Obstacle) -> None:
    world.say(shortcut.fails)
    if baboon.meters["wet"] >= THRESHOLD:
        world.say("Cold water dripped from his fur, and his fine brave words floated away downstream.")
    elif baboon.meters["scratched"] >= THRESHOLD:
        world.say("Sharp thorns tugged his fur and left him blinking back tears of surprise.")
    elif baboon.meters["muddy"] >= THRESHOLD:
        world.say("Mud painted his legs brown on brown, and pride no longer looked grand at all.")


def rescue(world: World, baboon: Entity, helper: Entity, fruit: Fruit, obstacle: Obstacle) -> None:
    baboon.meters["rescued"] += 1
    baboon.meters["crossed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{helper.label} did not laugh. {helper.pronoun().capitalize()} simply came close and {helper.attrs["rescue_text"]}.'
    )
    world.say(
        f"At last {baboon.id} reached {obstacle.far_side}. He picked a cluster of {fruit.label}, but before he ate one, "
        f"he turned back with warm cheeks."
    )


def apology_and_change(world: World, baboon: Entity, helper: Entity, fruit: Fruit) -> None:
    baboon.memes["humility"] += 1
    baboon.memes["joy"] += 1
    world.say(
        f'"I spoke proudly and acted foolishly," said {baboon.id}. "Thank you for helping me."'
    )
    world.say(
        f"He offered the first ripe {fruit.label[:-1] if fruit.label.endswith('s') else fruit.label} to {helper.label}, "
        f"and from then on the young baboon listened before leaping."
    )


def moral_ending(world: World, baboon: Entity, helper: Entity, outcome: str) -> None:
    if outcome == "listened":
        world.say(
            f"That evening, {baboon.id} sat quietly in the shade and remembered how much trouble a calm word can save."
        )
    else:
        world.say(
            f"That evening, {baboon.id} sat quietly beside {helper.label} with drying fur and a much steadier heart."
        )
    world.say(
        "Moral Value: humility. Lesson Learned: the one who listens to wise advice reaches the sweetest fruit."
    )


def tell(obstacle: Obstacle, shortcut: Shortcut, helper_cfg: Helper, fruit: Fruit,
         baboon_name: str = "Bobo", temperament: str = "proud") -> World:
    world = World()

    baboon = world.add(Entity(
        id=baboon_name,
        kind="character",
        type="baboon",
        label=baboon_name,
        role="hero",
        traits=[temperament],
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        traits=["wise", "patient"],
        attrs={
            "caution_style": helper_cfg.caution_style,
            "rescue_text": helper_cfg.rescue_text,
            "wisdom": helper_cfg.wisdom,
        },
    ))
    world.add(Entity(
        id="obstacle",
        type="obstacle",
        label=obstacle.label,
        attrs={
            "hazard": obstacle.hazard,
            "harm": obstacle.harm,
        },
    ))
    world.add(Entity(
        id="shortcut",
        type="shortcut",
        label=shortcut.label,
        attrs={
            "grip": shortcut_grip(shortcut.id),
        },
    ))
    world.add(Entity(
        id="fruit",
        type="fruit",
        label=fruit.label,
        attrs={},
    ))

    world.facts.update(
        obstacle=obstacle,
        shortcut=shortcut,
        helper_cfg=helper_cfg,
        fruit=fruit,
        temperament=temperament,
        predicted=predict_attempt(obstacle, shortcut),
    )

    introduce(world, baboon, fruit, obstacle)
    world.para()
    boast(world, baboon, shortcut)
    warning(world, helper, obstacle)

    if listen_first(temperament, helper_cfg):
        world.para()
        choose_wisely(world, baboon, helper, fruit, obstacle)
        outcome = "listened"
    else:
        world.para()
        defy(world, baboon, shortcut)
        stumble_scene(world, baboon, shortcut, obstacle)
        world.para()
        rescue(world, baboon, helper, fruit, obstacle)
        apology_and_change(world, baboon, helper, fruit)
        outcome = "learned"

    world.para()
    moral_ending(world, baboon, helper, outcome)

    world.facts.update(
        baboon=baboon,
        helper=helper,
        outcome=outcome,
        stumbled=baboon.meters["stumbled"] >= THRESHOLD,
        rescued=baboon.meters["rescued"] >= THRESHOLD,
        crossed=baboon.meters["crossed"] >= THRESHOLD,
        harm=obstacle.harm if baboon.meters[obstacle.harm] >= THRESHOLD else "",
    )
    return world


@dataclass
class StoryParams:
    obstacle: str
    shortcut: str
    helper: str
    fruit: str
    baboon_name: str
    temperament: str
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
    "tortoise": [
        (
            "Why is a tortoise often used as a symbol of patience in stories?",
            "A tortoise moves slowly and steadily, so storymakers often use one to show patience and careful thinking."
        )
    ],
    "hornbill": [
        (
            "Why can seeing from high up help someone choose a safe path?",
            "From high up, you can notice slippery places and sharp places more easily. A better view helps you make wiser choices."
        )
    ],
    "elephant": [
        (
            "Why is an elephant a good helper in a fable?",
            "An elephant is strong, but in a good fable strength is best when it is gentle. That makes the help feel safe instead of scary."
        )
    ],
    "water": [
        (
            "Why can smooth stones in water be slippery?",
            "Water makes stones slick, and rounded stones can roll under a foot. That is why careful steps matter near a creek."
        )
    ],
    "thorns": [
        (
            "Why should animals and people move carefully near thorns?",
            "Thorns are sharp and can catch skin or fur quickly. Going slowly helps you notice where to place your feet."
        )
    ],
    "mud": [
        (
            "Why is mud tricky to cross quickly?",
            "Mud can look soft and easy, but your feet may slide on it. Fast running in mud often makes balance worse."
        )
    ],
    "patience": [
        (
            "What does patience mean?",
            "Patience means waiting calmly and doing things carefully instead of rushing. It often keeps small problems from becoming big ones."
        )
    ],
    "humility": [
        (
            "What is humility?",
            "Humility means not thinking you know everything already. A humble person can listen, learn, and accept help."
        )
    ],
}
KNOWLEDGE_ORDER = ["humility", "patience", "tortoise", "hornbill", "elephant", "water", "thorns", "mud"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    obstacle = f["obstacle"]
    helper = f["helper_cfg"]
    fruit = f["fruit"]
    baboon = f["baboon"]
    return [
        f'Write a short fable for a young child about a baboon who wants {fruit.label} beyond a {obstacle.label}, and include a clear moral at the end.',
        f"Tell a fable where a young baboon named {baboon.id} must choose between pride and wise advice from {helper.label}.",
        f'Write a gentle animal story in fable style that teaches humility and patience, using the word "baboon".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    baboon = f["baboon"]
    helper = f["helper"]
    obstacle = f["obstacle"]
    shortcut = f["shortcut"]
    fruit = f["fruit"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a young baboon named {baboon.id} and {helper.label}, the wiser animal nearby. "
            f"The baboon wanted {fruit.label} and had to decide whether to listen."
        ),
        (
            f"Why did {baboon.id} want to cross the {obstacle.label}?",
            f"He wanted to reach {fruit.tree} on the far side. The smell and sight of the fruit made him eager enough to rush."
        ),
        (
            f"What warning did {helper.label} give?",
            f"{helper.label} warned that the danger in front of the baboon was real and that a careful path would be safer. "
            f"The warning was about how to cross without getting hurt or stuck."
        ),
    ]
    if f["outcome"] == "listened":
        qa.append((
            f"How did {baboon.id} solve the problem?",
            f"He stopped showing off and asked for the safe way across. Because he listened before leaping, he reached the fruit without a stumble."
        ))
        qa.append((
            f"What lesson did {baboon.id} learn?",
            "He learned that humility can save trouble before it starts. Listening to wisdom early is often easier than fixing a foolish mistake later."
        ))
    else:
        harm = f.get("harm") or "trouble"
        qa.append((
            f"What happened when {baboon.id} tried the shortcut?",
            f"He stumbled and ended up in {harm}. The mishap showed him that proud words do not make a risky path safe."
        ))
        qa.append((
            f"How did {helper.label} help after the stumble?",
            f"{helper.label} stayed kind and showed or made a safer way across instead of laughing. "
            f"That help let the baboon finish the journey and understand why the warning mattered."
        ))
        qa.append((
            f"What lesson did {baboon.id} learn at the end?",
            "He learned that pride can lead straight into trouble, while wise advice leads out of it. "
            "After being helped, he thanked the helper and chose to listen more carefully."
        ))
    qa.append((
        "What is the moral of the fable?",
        "The moral is that humility and patience lead to better endings than pride and haste. "
        "A listener often reaches the sweetest reward."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"humility", "patience"}
    helper_id = f["helper_cfg"].id
    obstacle_id = f["obstacle"].id
    helper_tag = {
        "tortoise": "tortoise",
        "hornbill": "hornbill",
        "elephant": "elephant",
    }[helper_id]
    obstacle_tag = {
        "creek": "water",
        "thorns": "thorns",
        "ditch": "mud",
    }[obstacle_id]
    tags.add(helper_tag)
    tags.add(obstacle_tag)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != "" and v is not None}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        obstacle="creek",
        shortcut="log",
        helper="tortoise",
        fruit="figs",
        baboon_name="Bobo",
        temperament="proud",
        seed=101,
    ),
    StoryParams(
        obstacle="thorns",
        shortcut="jump",
        helper="hornbill",
        fruit="mangoes",
        baboon_name="Kito",
        temperament="hasty",
        seed=102,
    ),
    StoryParams(
        obstacle="ditch",
        shortcut="stones",
        helper="elephant",
        fruit="plums",
        baboon_name="Mosi",
        temperament="thoughtful",
        seed=103,
    ),
    StoryParams(
        obstacle="creek",
        shortcut="stones",
        helper="hornbill",
        fruit="mangoes",
        baboon_name="Tamu",
        temperament="gentle",
        seed=104,
    ),
]


def explain_rejection(obstacle: Obstacle, shortcut: Shortcut, helper: Helper) -> str:
    if not shortcut_fits(shortcut, obstacle):
        supported = ", ".join(sorted(shortcut.works_for))
        return (
            f"(No story: {shortcut.label} is not a plausible shortcut for a {obstacle.label}. "
            f"It only fits: {supported}.)"
        )
    if not helper_can_solve(helper, obstacle):
        supported = ", ".join(sorted(helper.supports))
        return (
            f"(No story: {helper.label} cannot sensibly solve a {obstacle.label} in this world. "
            f"{helper.label} supports: {supported}.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
fits_shortcut(O, S) :- shortcut_works_for(S, O).
fits_helper(O, H)   :- helper_supports(H, O).

valid(O, S, H) :- obstacle(O), shortcut(S), helper(H),
                  fits_shortcut(O, S), fits_helper(O, H).

listened :- temperament(T), calm(T).
learned  :- temperament(T), rash(T).

outcome(listened) :- valid(_, _, _), listened.
outcome(learned)  :- valid(_, _, _), learned.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        for oid in sorted(shortcut.works_for):
            lines.append(asp.fact("shortcut_works_for", sid, oid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for oid in sorted(helper.supports):
            lines.append(asp.fact("helper_supports", hid, oid))
    lines.append(asp.fact("calm", "thoughtful"))
    lines.append(asp.fact("calm", "gentle"))
    lines.append(asp.fact("rash", "proud"))
    lines.append(asp.fact("rash", "hasty"))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("temperament", params.temperament),
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_shortcut", params.shortcut),
        asp.fact("chosen_helper", params.helper),
        "valid(O,S,H) :- chosen_obstacle(O), chosen_shortcut(S), chosen_helper(H), fits_shortcut(O,S), fits_helper(O,H).",
    ])
    model = asp.one_model(asp_program(scenario))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "listened" if listen_first(params.temperament, HELPERS[params.helper]) else "learned"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "baboon" not in sample.story.lower():
            raise StoryError("smoke test story missing expected content")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: normal generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable storyworld: a baboon, a risky shortcut, wise advice, and a moral lesson."
    )
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--baboon-name")
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.shortcut:
        obstacle = OBSTACLES[args.obstacle]
        shortcut = SHORTCUTS[args.shortcut]
        helper = HELPERS[args.helper] if args.helper else next(iter(HELPERS.values()))
        if not shortcut_fits(shortcut, obstacle):
            raise StoryError(explain_rejection(obstacle, shortcut, helper))
    if args.obstacle and args.helper:
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        shortcut = SHORTCUTS[args.shortcut] if args.shortcut else next(iter(SHORTCUTS.values()))
        if not helper_can_solve(helper, obstacle):
            raise StoryError(explain_rejection(obstacle, shortcut, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.obstacle is None or combo[0] == args.obstacle)
        and (args.shortcut is None or combo[1] == args.shortcut)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    obstacle_id, shortcut_id, helper_id = rng.choice(sorted(combos))
    fruit_id = args.fruit or rng.choice(sorted(FRUITS))
    name = args.baboon_name or rng.choice(BABOON_NAMES)
    temperament = args.temperament or rng.choice(TEMPERAMENTS)
    return StoryParams(
        obstacle=obstacle_id,
        shortcut=shortcut_id,
        helper=helper_id,
        fruit=fruit_id,
        baboon_name=name,
        temperament=temperament,
    )


def generate(params: StoryParams) -> StorySample:
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.fruit not in FRUITS:
        raise StoryError(f"(Unknown fruit: {params.fruit})")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(Unknown temperament: {params.temperament})")

    obstacle = OBSTACLES[params.obstacle]
    shortcut = SHORTCUTS[params.shortcut]
    helper = HELPERS[params.helper]
    if not shortcut_fits(shortcut, obstacle) or not helper_can_solve(helper, obstacle):
        raise StoryError(explain_rejection(obstacle, shortcut, helper))

    world = tell(
        obstacle=obstacle,
        shortcut=shortcut,
        helper_cfg=helper,
        fruit=FRUITS[params.fruit],
        baboon_name=params.baboon_name,
        temperament=params.temperament,
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
        print(f"{len(combos)} compatible (obstacle, shortcut, helper) combos:\n")
        for obstacle, shortcut, helper in combos:
            print(f"  {obstacle:8} {shortcut:8} {helper}")
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
            header = (
                f"### {p.baboon_name}: {p.obstacle}, {p.shortcut}, {p.helper}, "
                f"{p.temperament}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
