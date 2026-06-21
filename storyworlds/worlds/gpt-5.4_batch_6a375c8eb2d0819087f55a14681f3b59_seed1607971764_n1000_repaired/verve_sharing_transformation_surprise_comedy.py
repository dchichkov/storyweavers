#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/verve_sharing_transformation_surprise_comedy.py
===========================================================================

A standalone story world about two children making funny baked dough shapes.
The core story energy is:

- Sharing: one child first wants all the topping, then learns to share.
- Transformation: soft dough changes in the oven into a warm, puffy snack.
- Surprise: the baked shape comes out funnier than expected.
- Comedy: the turn is silly, physical, and affectionate rather than scary.

Run it
------
    python storyworlds/worlds/gpt-5.4/verve_sharing_transformation_surprise_comedy.py
    python storyworlds/worlds/gpt-5.4/verve_sharing_transformation_surprise_comedy.py --shape glasses --topping cheese
    python storyworlds/worlds/gpt-5.4/verve_sharing_transformation_surprise_comedy.py --shape crown --topping cheese
    python storyworlds/worlds/gpt-5.4/verve_sharing_transformation_surprise_comedy.py --all
    python storyworlds/worlds/gpt-5.4/verve_sharing_transformation_surprise_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/verve_sharing_transformation_surprise_comedy.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/verve_sharing_transformation_surprise_comedy.py --verify
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
SHAREFUL_TRAITS = {"generous", "thoughtful", "kind"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Project:
    id: str
    scene: str
    opener: str
    cheer: str
    ending: str
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
class ShapeConfig:
    id: str
    label: str
    raw_line: str
    kept_line: str
    flop_line: str
    surprise_pose: str
    capacity: int
    delicate: bool = False
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
class Topping:
    id: str
    label: str
    bowl_phrase: str
    sprinkle_line: str
    load: int
    chunky: bool = False
    sweet: bool = False
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


def _r_overload(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.type != "dough":
            continue
        if ent.meters["topping_load"] <= ent.attrs.get("capacity", 0):
            continue
        sig = ("overload", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["stability"] -= 1
        out.append("__overload__")
    return out


def _r_bake_result(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.type != "dough" or ent.meters["baked"] < THRESHOLD:
            continue
        if ent.meters["stability"] < 0:
            sig = ("flop", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                ent.meters["flopped"] += 1
                out.append("__flop__")
        else:
            sig = ("kept", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                ent.meters["kept_shape"] += 1
                out.append("__kept__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.type != "dough":
            continue
        if ent.meters["flopped"] < THRESHOLD and ent.meters["kept_shape"] < THRESHOLD:
            continue
        sig = ("surprise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.kids():
            kid.memes["surprise"] += 1
            kid.memes["joy"] += 1
        out.append("__surprise__")
    return out


def _r_sharing(world: World) -> list[str]:
    bowl = world.entities.get("bowl")
    if bowl is None or bowl.meters["shared"] < THRESHOLD:
        return []
    sig = ("sharing", "bowl")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fairness"] += 1
        kid.memes["warmth"] += 1
    return ["__shared__"]


CAUSAL_RULES = [
    Rule(name="overload", tag="physical", apply=_r_overload),
    Rule(name="bake_result", tag="physical", apply=_r_bake_result),
    Rule(name="surprise", tag="emotional", apply=_r_surprise),
    Rule(name="sharing", tag="social", apply=_r_sharing),
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


def topping_fits(shape: ShapeConfig, topping: Topping) -> bool:
    return not (shape.delicate and topping.chunky)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for project_id in PROJECTS:
        for topping_id, topping in TOPPINGS.items():
            for shape_id, shape in SHAPES.items():
                if topping_fits(shape, topping):
                    combos.append((project_id, topping_id, shape_id))
    return combos


def would_share_early(relation: str, hero_age: int, friend_age: int, trait: str) -> bool:
    if trait in SHAREFUL_TRAITS:
        return True
    return relation == "siblings" and friend_age > hero_age


def flop_if_not_shared(shape: ShapeConfig, topping: Topping) -> bool:
    return topping.load * 2 > shape.capacity


def outcome_of(params: "StoryParams") -> str:
    if would_share_early(params.relation, params.hero_age, params.friend_age, params.trait):
        return "shared_early"
    if flop_if_not_shared(SHAPES[params.shape], TOPPINGS[params.topping]):
        return "flop_then_share"
    return "share_late"


def predict_bake(world: World, shared: bool) -> dict:
    sim = world.copy()
    hero_dough = sim.get("hero_dough")
    friend_dough = sim.get("friend_dough")
    topping = sim.facts["topping_cfg"]
    share_amount = topping.load
    if shared:
        hero_dough.meters["topping_load"] += share_amount
        friend_dough.meters["topping_load"] += share_amount
        sim.get("bowl").meters["shared"] += 1
    else:
        hero_dough.meters["topping_load"] += share_amount * 2
    hero_dough.meters["baked"] += 1
    friend_dough.meters["baked"] += 1
    propagate(sim, narrate=False)
    return {
        "hero_flopped": hero_dough.meters["flopped"] >= THRESHOLD,
        "friend_flopped": friend_dough.meters["flopped"] >= THRESHOLD,
        "shared": sim.get("bowl").meters["shared"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, project: Project, shape: ShapeConfig) -> None:
    for kid in (hero, friend):
        kid.memes["joy"] += 1
    world.say(
        f"After lunch, {hero.id} and {friend.id} rushed into the kitchen with so much verve "
        f"that even the wooden spoons seemed ready to dance. They turned the table into {project.scene}."
    )
    world.say(project.opener)
    world.say(
        f'"{project.cheer}!" {hero.id} said, pinching and rolling the dough until it looked like {shape.raw_line}.'
    )


def ask_to_share(world: World, hero: Entity, friend: Entity, topping: Topping) -> None:
    friend.memes["hope"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"Beside the dough sat {topping.bowl_phrase}. {friend.id} leaned closer and asked, "
        f'"Can we share {topping.label} so both of ours can sparkle?"'
    )


def refuse(world: World, hero: Entity, topping: Topping) -> None:
    hero.memes["greed"] += 1
    world.say(
        f'{hero.id} hugged the bowl to {hero.pronoun("possessive")} chest. '
        f'"I need every bit of {topping.label} for my own one," {hero.pronoun()} declared.'
    )


def warn(world: World, parent: Entity, hero: Entity, friend: Entity, shape: ShapeConfig, topping: Topping) -> None:
    no_share = predict_bake(world, shared=False)
    yes_share = predict_bake(world, shared=True)
    world.facts["predicted_flop_without_share"] = no_share["hero_flopped"]
    world.facts["predicted_keep_with_share"] = not yes_share["hero_flopped"]
    if no_share["hero_flopped"] and yes_share["shared"]:
        world.say(
            f'{parent.label_word.capitalize()} looked at the wobbly dough and said, '
            f'"Too much {topping.label} can make {shape.label} dough slump. If you share the bowl, '
            f"both shapes can stay themselves."
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} tapped the tray and said, '
            f'"A little on each works better than a mountain on one."'
        )
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} nodded. "Two funny snacks are better than one bossy snack," {friend.pronoun()} said.'
    )


def share_early(world: World, hero: Entity, friend: Entity, topping: Topping) -> None:
    hero.memes["greed"] = 0.0
    hero.memes["fairness"] += 1
    friend.memes["relief"] += 1
    bowl = world.get("bowl")
    bowl.meters["shared"] += 1
    world.say(
        f"{hero.id} looked at the small bowl, then at {friend.id}'s plain dough, and sighed. "
        f'"All right. Half for you, half for me."'
    )
    world.say(
        f"They tipped {topping.label} into two little piles and {topping.sprinkle_line} with very serious faces."
    )
    propagate(world, narrate=False)


def hog_topping(world: World, hero: Entity, topping: Topping) -> None:
    hero_dough = world.get("hero_dough")
    hero_dough.meters["topping_load"] += topping.load * 2
    world.say(
        f"{hero.id} shook on so much {topping.label} that the dough looked as if it were wearing a crunchy blanket."
    )
    propagate(world, narrate=False)


def shape_plain_friend(world: World, friend: Entity, shape: ShapeConfig) -> None:
    world.say(
        f"{friend.id} kept shaping the plain dough anyway, trying very hard to make {shape.label} without any sparkle at all."
    )


def bake(world: World, parent: Entity) -> None:
    hero_dough = world.get("hero_dough")
    friend_dough = world.get("friend_dough")
    hero_dough.meters["baked"] += 1
    friend_dough.meters["baked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon the tray slid into the oven. Through the little glass door, the dough puffed, browned, and changed from soft loops into real warm snacks."
    )
    world.say(
        f'The kitchen filled with a cozy smell, and even {parent.label_word} stood on tiptoe for the big reveal.'
    )


def reveal_good(world: World, hero: Entity, friend: Entity, shape: ShapeConfig) -> None:
    hero_dough = world.get("hero_dough")
    friend_dough = world.get("friend_dough")
    hero_dough.meters["surprise_named"] += 1
    friend_dough.meters["surprise_named"] += 1
    world.say(
        f"When the tray came out, both pieces had held their shapes. {shape.kept_line}"
    )
    world.say(
        f"For one blinking second, the children were too surprised to speak. Then they both burst out laughing and tried {shape.surprise_pose}."
    )


def reveal_flop(world: World, hero: Entity, friend: Entity, shape: ShapeConfig) -> None:
    hero_dough = world.get("hero_dough")
    hero_dough.meters["surprise_named"] += 1
    friend.memes["sympathy"] += 1
    hero.memes["embarrassment"] += 1
    world.say(
        f"When the tray came out, {hero.id}'s piece had forgotten the plan completely. {shape.flop_line}"
    )
    world.say(
        f"{friend.id} stared, then snorted, then tried not to laugh and failed. Soon even {hero.id} was giggling, because the silly thing looked too ridiculous to stay mad at."
    )


def late_share_after_flop(world: World, hero: Entity, friend: Entity, topping: Topping) -> None:
    bowl = world.get("bowl")
    bowl.meters["shared"] += 1
    hero.memes["fairness"] += 1
    friend.memes["relief"] += 1
    world.say(
        f'{hero.id} broke off the funniest puffed corner and held it out. '
        f'"Here. The best part should be shared," {hero.pronoun()} said.'
    )
    world.say(
        f"{friend.id} grinned, and together they sprinkled the last dusty bits of {topping.label} over both warm pieces."
    )
    propagate(world, narrate=False)


def late_share_good(world: World, hero: Entity, friend: Entity, shape: ShapeConfig, topping: Topping) -> None:
    bowl = world.get("bowl")
    bowl.meters["shared"] += 1
    hero.memes["fairness"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"When the tray came out, {hero.id}'s snack had kept its shape so perfectly that it looked almost too proud to eat. "
        f"{shape.kept_line}"
    )
    world.say(
        f"That made {hero.id} look over at {friend.id}'s plain one and finally notice the lonely side of the tray."
    )
    world.say(
        f'{hero.id} pushed the bowl across the table. "Let\'s fix that," {hero.pronoun()} said. '
        f"Together they added the last of the {topping.label} and traded bites."
    )
    propagate(world, narrate=False)


def ending(world: World, hero: Entity, friend: Entity, project: Project, shape: ShapeConfig) -> None:
    for kid in (hero, friend):
        kid.memes["joy"] += 1
        kid.memes["warmth"] += 1
    world.say(
        f"In the end, crumbs landed everywhere except the plate. {project.ending}"
    )
    world.say(
        f"By the last bite, {hero.id} and {friend.id} were leaning together, smiling with warm cheeks and silly mouths, and the kitchen felt brighter because the snack had been shared."
    )
    world.facts["ending_image"] = shape.surprise_pose
@dataclass
class StoryParams:
    project: str
    topping: str
    shape: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    hero_age: int = 5
    friend_age: int = 6
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
    "dough": [
        (
            "What happens to dough in an oven?",
            "Heat makes dough puff, firm up, and turn golden. That is why a soft shape can change so much while it bakes."
        )
    ],
    "sharing": [
        (
            "Why does sharing make a game feel better?",
            "Sharing lets more than one person join the fun, so everyone feels included. It can also turn a quarrel into laughter much faster."
        )
    ],
    "sesame": [
        (
            "What are sesame seeds?",
            "Sesame seeds are tiny little seeds people sprinkle on food. They add a nutty taste and a bit of crunch."
        )
    ],
    "cinnamon": [
        (
            "What is cinnamon sugar?",
            "Cinnamon sugar is sugar mixed with cinnamon, a warm-smelling spice. People use it to make food taste sweet and cozy."
        )
    ],
    "cheese": [
        (
            "Why does shredded cheese melt in the oven?",
            "Cheese softens and melts when it gets hot. That is why it can spread and turn stretchy on baked food."
        )
    ],
    "glasses": [
        (
            "Why are glasses-shaped snacks funny?",
            "They look like something for a face even though they are food. That silly mix-up can make people laugh."
        )
    ],
    "crown": [
        (
            "What is a crown?",
            "A crown is a fancy headpiece that kings, queens, or pretend rulers might wear. In play, a crown can make someone feel grand and silly at the same time."
        )
    ],
    "mustache": [
        (
            "Why is a pretend mustache a funny disguise?",
            "A pretend mustache can make an ordinary face look suddenly grand or ridiculous. Small disguises feel funny because they change how someone seems right away."
        )
    ],
    "snake": [
        (
            "Why can a snake shape curl when it bakes?",
            "Soft dough can puff and bend as heat moves through it. A long shape may curl more while it bakes."
        )
    ],
    "bakery": [
        (
            "What does a bakery make?",
            "A bakery makes breads, buns, cakes, and other baked treats. It often smells warm and toasty."
        )
    ],
    "circus": [
        (
            "What is a circus ring?",
            "A circus ring is the open place where performers do their acts. It is the center of the show."
        )
    ],
    "tea_party": [
        (
            "What is a tea party?",
            "A tea party is a small gathering with cups, snacks, and polite pretend manners. Children often make it playful and silly."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sharing", "dough", "sesame", "cinnamon", "cheese",
    "glasses", "crown", "mustache", "snake",
    "bakery", "circus", "tea_party",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    project = f["project_cfg"]
    topping = f["topping_cfg"]
    shape = f["shape_cfg"]
    outcome = f["outcome"]
    if outcome == "shared_early":
        return [
            f'Write a funny story for a 3-to-5-year-old that includes the word "verve" and shows two children baking {shape.label}, sharing {topping.label}, and laughing at the surprise result.',
            f"Tell a comedy where {hero.id} first wants all the {topping.label}, but shares before baking, and the dough transforms into a silly success.",
            f"Write a warm kitchen story set like {project.scene}, where sharing turns a possible quarrel into a cheerful surprise."
        ]
    if outcome == "flop_then_share":
        return [
            f'Write a child-friendly comedy with the word "verve" where one child hogs {topping.label}, the dough transforms into a ridiculous mistake, and the children end by sharing it anyway.',
            f"Tell a funny baking story where {hero.id}'s {shape.label} flops in the oven, causing a surprise that leads to laughter and sharing.",
            f"Write a short story about two children in a kitchen, a silly transformation, and a snack that becomes funnier after someone learns to share."
        ]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "verve", a baking transformation, and a moment when a child notices it is better to share.',
        f"Tell a comedy where {hero.id} keeps the {topping.label} at first, but changes heart after the snacks come out of the oven.",
        f"Write a warm, silly kitchen story with sharing, surprise, and a dough shape that turns out funnier than expected."
    ]


def relation_noun(hero: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "girl" and friend.type == "girl":
            return "two sisters"
        if hero.type == "boy" and friend.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    project = f["project_cfg"]
    topping = f["topping_cfg"]
    shape = f["shape_cfg"]
    relation = f["relation"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {relation_noun(hero, friend, relation)}, {hero.id} and {friend.id}, who were making a funny baked snack with {parent.label_word}. The story stays in the kitchen and follows how they went from grabbing to sharing."
        ),
        (
            "What were they trying to make?",
            f"They were shaping dough into {shape.label} as part of {project.scene}. The soft dough was meant to transform in the oven into a warm snack."
        ),
        (
            f"Why did {friend.id} ask to share the {topping.label}?",
            f"{friend.id} wanted both dough pieces to look special instead of only one. Sharing the topping would let both children join the same game, not leave one side of the tray plain."
        ),
    ]
    if f["predicted_flop_without_share"]:
        qa.append((
            f"What warning did {parent.label_word} give, and why?",
            f"{parent.label_word.capitalize()} warned that too much {topping.label} on one piece could make the dough slump. That warning came from the way extra weight can blur a delicate shape while it bakes."
        ))
    if outcome == "shared_early":
        qa.append((
            f"How did the problem get solved?",
            f"{hero.id} agreed to split the bowl before baking, so both children decorated their dough. Because they shared early, both snacks could keep their shapes and the surprise was happy instead of disappointing."
        ))
        qa.append((
            "What was the surprise?",
            f"When the tray came out, the dough had transformed neatly and looked even funnier than they expected. The children laughed because the baked shapes suddenly looked like a silly costume prop."
        ))
    elif outcome == "flop_then_share":
        qa.append((
            f"What happened to {hero.id}'s dough in the oven?",
            f"It puffed into the wrong shape and came out looking ridiculous. That happened because {hero.id} put too much {topping.label} on one piece before it baked."
        ))
        qa.append((
            f"How did sharing still happen at the end?",
            f"After the funny flop, {hero.id} shared the best piece with {friend.id}. The mistake changed the mood, because laughing together made it easier to stop being possessive."
        ))
    else:
        qa.append((
            f"Why did {hero.id} decide to share later?",
            f"When the baked snack came out looking so proud and funny, {hero.id} finally noticed {friend.id}'s plain one. Seeing the lonely other side of the tray made sharing feel more important than keeping all the topping."
        ))
        qa.append((
            "How did the ending show that things changed?",
            f"By the end, they were trading bites and laughing together instead of guarding the bowl. The final crumbs and smiles prove the kitchen game ended in sharing, not in a quarrel."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sharing", "dough"} | set(f["project_cfg"].tags) | set(f["shape_cfg"].tags) | set(f["topping_cfg"].tags)
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
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != 0 and v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="bakery",
        topping="cinnamon_sugar",
        shape="glasses",
        hero_name="Mia",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        trait="thoughtful",
        relation="siblings",
        hero_age=5,
        friend_age=7,
    ),
    StoryParams(
        project="circus",
        topping="cheese",
        shape="mustache",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Lily",
        friend_gender="girl",
        parent="father",
        trait="bossy",
        relation="friends",
        hero_age=6,
        friend_age=6,
    ),
    StoryParams(
        project="tea_party",
        topping="sesame",
        shape="crown",
        hero_name="Ava",
        hero_gender="girl",
        friend_name="Nora",
        friend_gender="girl",
        parent="mother",
        trait="eager",
        relation="siblings",
        hero_age=7,
        friend_age=5,
    ),
    StoryParams(
        project="circus",
        topping="sesame",
        shape="snake",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Eli",
        friend_gender="boy",
        parent="father",
        trait="kind",
        relation="friends",
        hero_age=5,
        friend_age=5,
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
valid(P, T, S) :- project(P), topping(T), shape(S), not bad_combo(T, S).
bad_combo(T, S) :- chunky(T), delicate(S).

% --- outcome model ----------------------------------------------------------
share_early :- trait(T), shareful(T).
share_early :- relation(siblings), friend_age(FA), hero_age(HA), FA > HA.

flop_if_greedy :- chosen_topping(T), chosen_shape(S), load(T, L), capacity(S, C), 2 * L > C.

outcome(shared_early) :- share_early.
outcome(flop_then_share) :- not share_early, flop_if_greedy.
outcome(share_late) :- not share_early, not flop_if_greedy.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    for topping_id, topping in TOPPINGS.items():
        lines.append(asp.fact("topping", topping_id))
        lines.append(asp.fact("load", topping_id, topping.load))
        if topping.chunky:
            lines.append(asp.fact("chunky", topping_id))
    for shape_id, shape in SHAPES.items():
        lines.append(asp.fact("shape", shape_id))
        lines.append(asp.fact("capacity", shape_id, shape.capacity))
        if shape.delicate:
            lines.append(asp.fact("delicate", shape_id))
    for trait in sorted(SHAREFUL_TRAITS):
        lines.append(asp.fact("shareful", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_topping", params.topping),
        asp.fact("chosen_shape", params.shape),
        asp.fact("trait", params.trait),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("friend_age", params.friend_age),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
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
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(smoke, trace=False, qa=True, header="### smoke")
        if "smoke" not in buf.getvalue():
            raise StoryError("emit() smoke output missing header")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: two children bake a funny snack, and sharing changes the ending."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--topping", choices=TOPPINGS)
    ap.add_argument("--shape", choices=SHAPES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.topping and args.shape:
        topping = TOPPINGS[args.topping]
        shape = SHAPES[args.shape]
        if not topping_fits(shape, topping):
            raise StoryError(explain_rejection(topping, shape))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.topping is None or combo[1] == args.topping)
        and (args.shape is None or combo[2] == args.shape)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, topping_id, shape_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=hero_name)
    relation = args.relation or rng.choice(["siblings", "friends"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    hero_age, friend_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        project=project_id,
        topping=topping_id,
        shape=shape_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        friend_age=friend_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.topping not in TOPPINGS:
        raise StoryError(f"(Unknown topping: {params.topping})")
    if params.shape not in SHAPES:
        raise StoryError(f"(Unknown shape: {params.shape})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.relation not in {"siblings", "friends"}:
        raise StoryError(f"(Unknown relation: {params.relation})")
    shape = SHAPES[params.shape]
    topping = TOPPINGS[params.topping]
    if not topping_fits(shape, topping):
        raise StoryError(explain_rejection(topping, shape))

    world = tell(
        PROJECTS[params.project],
        topping,
        shape,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
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
        print(f"{len(combos)} compatible (project, topping, shape) combos:\n")
        for project_id, topping_id, shape_id in combos:
            print(f"  {project_id:10} {topping_id:16} {shape_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.hero_name} & {p.friend_name}: {p.shape} with {p.topping} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    project: Project,
    topping: Topping,
    shape: ShapeConfig,
    *,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "thoughtful",
    relation: str = "siblings",
    hero_age: int = 5,
    friend_age: int = 6,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        age=friend_age,
        traits=["patient"],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    bowl = world.add(Entity(
        id="bowl",
        type="bowl",
        label=topping.label,
        tags=set(topping.tags),
    ))
    hero_dough = world.add(Entity(
        id="hero_dough",
        type="dough",
        label=f"{hero_name}'s dough",
        attrs={"capacity": shape.capacity, "shape": shape.id},
        tags={"dough"} | set(shape.tags),
    ))
    friend_dough = world.add(Entity(
        id="friend_dough",
        type="dough",
        label=f"{friend_name}'s dough",
        attrs={"capacity": shape.capacity, "shape": shape.id},
        tags={"dough"} | set(shape.tags),
    ))

    for ent in (hero_dough, friend_dough):
        ent.meters["stability"] = 0.0
        ent.meters["topping_load"] = 0.0
        ent.meters["baked"] = 0.0
        ent.meters["flopped"] = 0.0
        ent.meters["kept_shape"] = 0.0
    bowl.meters["shared"] = 0.0

    world.facts.update(
        project_cfg=project,
        topping_cfg=topping,
        shape_cfg=shape,
        hero=hero,
        friend=friend,
        parent=parent,
        bowl=bowl,
        hero_dough=hero_dough,
        friend_dough=friend_dough,
        relation=relation,
        trait=trait,
        predicted_flop_without_share=False,
        predicted_keep_with_share=False,
    )

    introduce(world, hero, friend, project, shape)
    ask_to_share(world, hero, friend, topping)

    world.para()
    refuse(world, hero, topping)
    warn(world, parent, hero, friend, shape, topping)

    outcome = "shared_early" if would_share_early(relation, hero_age, friend_age, trait) else (
        "flop_then_share" if flop_if_not_shared(shape, topping) else "share_late"
    )

    world.para()
    if outcome == "shared_early":
        share_early(world, hero, friend, topping)
        world.get("hero_dough").meters["topping_load"] += topping.load
        world.get("friend_dough").meters["topping_load"] += topping.load
        bake(world, parent)
        reveal_good(world, hero, friend, shape)
    elif outcome == "flop_then_share":
        hog_topping(world, hero, topping)
        shape_plain_friend(world, friend, shape)
        bake(world, parent)
        reveal_flop(world, hero, friend, shape)
        world.para()
        late_share_after_flop(world, hero, friend, topping)
    else:
        hog_topping(world, hero, topping)
        shape_plain_friend(world, friend, shape)
        bake(world, parent)
        late_share_good(world, hero, friend, shape, topping)

    world.para()
    ending(world, hero, friend, project, shape)

    world.facts.update(
        outcome=outcome,
        shared=world.get("bowl").meters["shared"] >= THRESHOLD,
        hero_flopped=world.get("hero_dough").meters["flopped"] >= THRESHOLD,
        friend_flopped=world.get("friend_dough").meters["flopped"] >= THRESHOLD,
        hero_kept_shape=world.get("hero_dough").meters["kept_shape"] >= THRESHOLD,
        friend_kept_shape=world.get("friend_dough").meters["kept_shape"] >= THRESHOLD,
    )
    return world


PROJECTS = {
    "bakery": Project(
        id="bakery",
        scene="a tiny bakery with floury elbows and a rattly old cooling rack",
        opener="A floured towel became the grand bakery counter, and the empty muffin tin became the audience.",
        cheer="Fast hands! Fancy snacks",
        ending="The cooling rack looked less like a bakery now and more like a tiny picnic after a very funny parade.",
        tags={"bakery", "sharing"},
    ),
    "circus": Project(
        id="circus",
        scene="a miniature circus where the tray was the ring and the oven was the drumroll",
        opener="A dish towel became the circus curtain, and the rolling pin waited like a ringmaster's baton.",
        cheer="Snack circus, begin",
        ending="The circus ended with crumbs, bows, and one napkin doing the work of a whole mop.",
        tags={"circus", "sharing"},
    ),
    "tea_party": Project(
        id="tea_party",
        scene="the grandest tea party in the world, even though the guests were only two children and a wobbling sugar bowl",
        opener="The cups were lined up in a row, and the butter knife was invited as a very serious duke.",
        cheer="Tea party treats",
        ending="By the time the plates were empty, the tea party had become a laughing party instead.",
        tags={"tea_party", "sharing"},
    ),
}

SHAPES = {
    "glasses": ShapeConfig(
        id="glasses",
        label="pretend glasses",
        raw_line="two careful loops with a tiny bridge in the middle",
        kept_line="They looked like golden glasses for a giant with a very polite face.",
        flop_line="It had puffed into one plump, lopsided mask with no sensible nose place at all.",
        surprise_pose="holding the warm loops up in front of their eyes and pretending to look terribly wise",
        capacity=1,
        delicate=True,
        tags={"glasses", "dough"},
    ),
    "crown": ShapeConfig(
        id="crown",
        label="a dough crown",
        raw_line="a little crown with brave pointy tips",
        kept_line="The points stood up proudly, as if the crown had just remembered it was royal.",
        flop_line="The points had melted into a sleepy hat that looked ready for a nap instead of a throne.",
        surprise_pose="taking turns balancing the warm crown above their eyebrows and bowing to the toaster",
        capacity=1,
        delicate=True,
        tags={"crown", "dough"},
    ),
    "mustache": ShapeConfig(
        id="mustache",
        label="a dough mustache",
        raw_line="a curly mustache with dramatic ends",
        kept_line="It came out looking like the sort of mustache a walrus might wear to a dance.",
        flop_line="It had swollen into a cheerful caterpillar with ideas far too big for its own face.",
        surprise_pose="holding the snack under their noses and speaking in grand, booming voices",
        capacity=2,
        delicate=False,
        tags={"mustache", "dough"},
    ),
    "snake": ShapeConfig(
        id="snake",
        label="a dough snake",
        raw_line="a long noodle snake with a twisty tail",
        kept_line="It curled on the tray like a smug little snake that knew it smelled delicious.",
        flop_line="It had puffed into a short, chubby worm that looked surprised to be alive.",
        surprise_pose="making the snake wiggle through the air before taking silly little bites",
        capacity=2,
        delicate=False,
        tags={"snake", "dough"},
    ),
}

TOPPINGS = {
    "sesame": Topping(
        id="sesame",
        label="sesame seeds",
        bowl_phrase="a blue bowl of sesame seeds",
        sprinkle_line="sprinkled the tiny seeds over both shapes",
        load=1,
        chunky=False,
        sweet=False,
        tags={"sesame", "sharing"},
    ),
    "cinnamon_sugar": Topping(
        id="cinnamon_sugar",
        label="cinnamon sugar",
        bowl_phrase="a little bowl of cinnamon sugar that smelled like a warm cloud",
        sprinkle_line="dusted both pieces until they looked gently sparkly",
        load=1,
        chunky=False,
        sweet=True,
        tags={"cinnamon", "sharing"},
    ),
    "cheese": Topping(
        id="cheese",
        label="shredded cheese",
        bowl_phrase="a yellow bowl of shredded cheese",
        sprinkle_line="laid the soft shreds across both shapes in neat little pinches",
        load=2,
        chunky=True,
        sweet=False,
        tags={"cheese", "sharing"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Finn", "Noah", "Eli"]
TRAITS = ["generous", "thoughtful", "kind", "bossy", "sparky", "eager"]


def explain_rejection(topping: Topping, shape: ShapeConfig) -> str:
    return (
        f"(No story: {topping.label} are too chunky for {shape.label}. "
        f"That shape needs a lighter topping so it can keep its form in the oven.)"
    )

if __name__ == "__main__":
    main()
