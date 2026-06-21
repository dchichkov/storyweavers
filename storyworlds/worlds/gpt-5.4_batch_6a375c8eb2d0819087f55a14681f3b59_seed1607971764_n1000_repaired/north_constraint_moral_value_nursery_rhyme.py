#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/north_constraint_moral_value_nursery_rhyme.py
========================================================================

A standalone story world for a gentle nursery-rhyme-style moral tale:
a small child sees something lovely near the north side of the garden,
but a real constraint stands in the way. The child must choose between
an impatient shortcut and a patient, kind solution.

This world models:
- typed entities with physical meters and emotional memes
- a short causal chain with a reasonableness gate
- state-driven nursery-rhyme prose
- grounded prompts, story QA, and world-knowledge QA
- an inline ASP twin for the compatibility gate and outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/north_constraint_moral_value_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/north_constraint_moral_value_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/north_constraint_moral_value_nursery_rhyme.py --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/north_constraint_moral_value_nursery_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4/north_constraint_moral_value_nursery_rhyme.py --asp
    python storyworlds/worlds/gpt-5.4/north_constraint_moral_value_nursery_rhyme.py --verify
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
KIND_MIN = 2


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
        female = {"girl", "mother", "hen", "goose", "ewe"}
        male = {"boy", "father", "gander", "ram", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
class Prize:
    id: str
    label: str
    phrase: str
    sound: str
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
class Boundary:
    id: str
    label: str
    phrase: str
    blocks: str
    rhyme: str
    harm: str
    trouble: str
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
class Method:
    id: str
    label: str
    phrase: str
    works_for: set[str] = field(default_factory=set)
    kind: int = 0
    follow_rule: bool = True
    action: str = ""
    qa_text: str = ""
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


def _r_temptation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["shortcut"] < THRESHOLD:
        return out
    sig = ("temptation", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["impatience"] += 1
    if "friend" in world.entities:
        world.get("friend").memes["worry"] += 1
    out.append("__temptation__")
    return out


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["snagged"] < THRESHOLD:
        return out
    sig = ("trouble", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["regret"] += 1
    if "friend" in world.entities:
        world.get("friend").memes["worry"] += 1
    out.append("__trouble__")
    return out


CAUSAL_RULES = [
    Rule(name="temptation", tag="social", apply=_r_temptation),
    Rule(name="trouble", tag="social", apply=_r_trouble),
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


def method_works(boundary: Boundary, method: Method) -> bool:
    return boundary.id in method.works_for


def is_kind(method: Method) -> bool:
    return method.kind >= KIND_MIN and method.follow_rule


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for prize_id in PRIZES:
        for boundary_id, boundary in BOUNDARIES.items():
            for method_id, method in METHODS.items():
                if method_works(boundary, method) and is_kind(method):
                    combos.append((prize_id, boundary_id, method_id))
    return combos


def predict_trouble(world: World, boundary: Boundary) -> dict:
    sim = world.copy()
    sim.get("hero").meters["snagged"] += 1 if boundary.id == "thorn_patch" else 0
    sim.get("hero").meters["muddy"] += 1 if boundary.id == "mud_rut" else 0
    propagate(sim, narrate=False)
    return {
        "snagged": sim.get("hero").meters["snagged"] >= THRESHOLD,
        "muddy": sim.get("hero").meters["muddy"] >= THRESHOLD,
        "worry": sim.get("friend").memes["worry"] if "friend" in sim.entities else 0.0,
    }


def opening(world: World, hero: Entity, friend: Entity, prize: Prize) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Little {hero.id} and little {friend.id}, in the soft sun's golden light, "
        f"sang in the garden, morning-bright."
    )
    world.say(
        f"{prize.phrase.capitalize()} gave {prize.sound}, so clear and so warm, "
        f"as the breeze skipped north across the farm."
    )


def drift_north(world: World, prize: Prize, boundary: Boundary) -> None:
    world.facts["north_place"] = "the north side of the garden"
    world.say(
        f"Up to the north side it twirled away, and there by {boundary.phrase} it lay."
    )
    world.say(
        f"But between the children and the prize stood {boundary.phrase}, "
        f"a real constraint for little feet that day."
    )


def longing(world: World, hero: Entity, prize: Prize) -> None:
    hero.memes["desire"] += 1
    world.say(
        f'"Oh dear," said {hero.id}, "I want my {prize.label} soon. '
        f'I want it back before the noon."'
    )


def warning(world: World, friend: Entity, hero: Entity, boundary: Boundary) -> None:
    pred = predict_trouble(world, boundary)
    world.facts["predicted_snagged"] = pred["snagged"]
    world.facts["predicted_muddy"] = pred["muddy"]
    friend.memes["care"] += 1
    extra = boundary.harm
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head and softly said, '
        f'"Not through there, {hero.id}. {extra}"'
    )


def shortcut_choice(world: World, hero: Entity, boundary: Boundary) -> None:
    hero.memes["shortcut"] += 1
    propagate(world, narrate=False)
    line = {
        "thorn_patch": f'But {hero.id} hopped toward the thorny side, hoping for one quick squeeze and stride.',
        "mud_rut": f'But {hero.id} skipped toward the muddy lane, thinking one fast dash would do the gain.',
        "sleeping_geese": f'But {hero.id} tiptoed near the geese in a row, hoping the way would stay soft and slow.',
    }[boundary.id]
    world.say(line)


def trouble(world: World, hero: Entity, friend: Entity, boundary: Boundary) -> None:
    if boundary.id == "thorn_patch":
        hero.meters["snagged"] += 1
        hero.meters["torn_hem"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Snip went a briar at hem and shoe; {hero.id} stopped still and could not get through."
        )
    elif boundary.id == "mud_rut":
        hero.meters["muddy"] += 1
        hero.meters["slipped"] += 1
        hero.memes["regret"] += 1
        friend.memes["worry"] += 1
        world.say(
            f"Squish went the rut. One foot sank deep, and muddy tears began to creep."
        )
    else:
        hero.meters["honked_at"] += 1
        hero.memes["fear"] += 1
        friend.memes["worry"] += 1
        world.say(
            f"Honk, honk, honk! The geese woke wide. {hero.id} jumped back from the flapping tide."
        )
    world.say(f'"Oh!" cried {hero.id}. "I should have stayed where kind rules guide the games we play."')


def helper_arrives(world: World, parent: Entity) -> None:
    parent.memes["care"] += 1
    world.say(
        f"Then came {parent.label_word} with patient tread, hearing the little words that had been said."
    )


def safe_recovery(world: World, parent: Entity, hero: Entity, prize: Prize, method: Method) -> None:
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    hero.memes["gratitude"] += 1
    if "friend" in world.entities:
        world.get("friend").memes["relief"] += 1
    world.facts["used_method"] = method.id
    world.say(
        f'{parent.label_word.capitalize()} smiled and said, "A rule can be a kindly guide; '
        f'constraint is what helps care and patience walk beside."'
    )
    world.say(
        f"Then {parent.pronoun()} {method.action}, and soon the little song was heard again: "
        f"{prize.sound}."
    )
    world.say(
        f"{hero.id} held the {prize.label} close and bright, and thanked {parent.label_word} with pure delight."
    )


def rhyme_lesson(world: World, hero: Entity, friend: Entity, boundary: Boundary, prize: Prize) -> None:
    world.say(
        f'{friend.id} and {hero.id} sang low and clear, "Slow steps save both flower and ear."'
    )
    world.say(
        f"From then on, when north winds called them on, they remembered the constraint and chose the gentle path before the song was gone."
    )
    if boundary.id == "thorn_patch":
        world.say("So briar stayed in the hedge, not in their clothes, and kindness bloomed beside the rose.")
    elif boundary.id == "mud_rut":
        world.say("So the path stayed neat, their paws stayed clean, and patient hearts kept all serene.")
    else:
        world.say("So the geese slept sound, the garden stayed mild, and careful manners crowned the child.")


def tell(
    *,
    prize: Prize,
    boundary: Boundary,
    method: Method,
    hero_name: str,
    hero_type: str,
    friend_name: str,
    friend_type: str,
    parent_type: str,
    shortcut: bool,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="prize", type="prize", label=prize.label))
    world.add(Entity(id="boundary", type="boundary", label=boundary.label))

    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    hero.memes["desire"] = 0.0
    hero.memes["shortcut"] = 0.0
    hero.memes["impatience"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["regret"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["lesson"] = 0.0
    hero.memes["gratitude"] = 0.0
    friend.memes["care"] = 0.0
    friend.memes["worry"] = 0.0
    friend.memes["relief"] = 0.0
    parent.memes["care"] = 0.0

    hero.meters["snagged"] = 0.0
    hero.meters["muddy"] = 0.0
    hero.meters["slipped"] = 0.0
    hero.meters["honked_at"] = 0.0
    hero.meters["torn_hem"] = 0.0

    world.facts["boundary"] = boundary
    world.facts["prize_cfg"] = prize
    world.facts["method"] = method
    world.facts["shortcut"] = shortcut

    opening(world, hero, friend, prize)
    drift_north(world, prize, boundary)

    world.para()
    longing(world, hero, prize)
    warning(world, friend, hero, boundary)

    if shortcut:
        shortcut_choice(world, hero, boundary)
        world.para()
        trouble(world, hero, friend, boundary)
        outcome = "trouble"
    else:
        world.say(
            f'{hero.id} took one breath, then two, and said, "I will not rush. I will be true."'
        )
        outcome = "obedient"

    world.para()
    helper_arrives(world, parent)
    safe_recovery(world, parent, hero, prize, method)
    rhyme_lesson(world, hero, friend, boundary, prize)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        prize=prize,
        boundary=boundary,
        outcome=outcome,
        resolved=True,
        troubled=outcome == "trouble",
    )
    return world


PRIZES = {
    "bell": Prize(
        id="bell",
        label="bell",
        phrase="a silver bell on a blue string",
        sound="ting-a-ling, ting-a-ling",
        tags={"bell", "north"},
    ),
    "bonnet": Prize(
        id="bonnet",
        label="bonnet",
        phrase="a butter-yellow bonnet with a ribbon brim",
        sound="swish went the ribbon in the wind",
        tags={"hat", "north"},
    ),
    "pinwheel": Prize(
        id="pinwheel",
        label="pinwheel",
        phrase="a striped pinwheel on a little stick",
        sound="whirr-a-whirl, whirr-a-whirl",
        tags={"wind", "north"},
    ),
}

BOUNDARIES = {
    "thorn_patch": Boundary(
        id="thorn_patch",
        label="thorn patch",
        phrase="the thorn patch by the rose hedge",
        blocks="squeezing through",
        rhyme="thorn",
        harm="The thorn patch will catch your hem and prick your step.",
        trouble="snagged",
        tags={"thorn", "constraint", "garden"},
    ),
    "mud_rut": Boundary(
        id="mud_rut",
        label="mud rut",
        phrase="the muddy rut by the cart lane",
        blocks="dashing across",
        rhyme="mud",
        harm="The muddy rut will grab your foot and spoil your play.",
        trouble="muddy",
        tags={"mud", "constraint", "garden"},
    ),
    "sleeping_geese": Boundary(
        id="sleeping_geese",
        label="sleeping geese",
        phrase="the sleeping geese beside the fence",
        blocks="tiptoeing past",
        rhyme="geese",
        harm="The geese need quiet; rushing there would wake and frighten them.",
        trouble="honked",
        tags={"geese", "constraint", "kindness"},
    ),
}

METHODS = {
    "garden_path": Method(
        id="garden_path",
        label="garden path",
        phrase="the round garden path",
        works_for={"thorn_patch", "mud_rut", "sleeping_geese"},
        kind=3,
        follow_rule=True,
        action="led them by the round garden path, all pebbled and neat",
        qa_text="used the round garden path",
        tags={"path", "patience"},
    ),
    "long_hook": Method(
        id="long_hook",
        label="long hook",
        phrase="a long willow hook",
        works_for={"thorn_patch", "mud_rut"},
        kind=3,
        follow_rule=True,
        action="reached with a long willow hook and lifted the prize back over the safe side",
        qa_text="used a long willow hook to lift it back",
        tags={"tool", "care"},
    ),
    "grain_bowl": Method(
        id="grain_bowl",
        label="grain bowl",
        phrase="a little grain bowl",
        works_for={"sleeping_geese"},
        kind=2,
        follow_rule=True,
        action="set down a little grain bowl far from the fence, and while the geese waddled kindly that way, picked up the prize from the quiet grass",
        qa_text="used a grain bowl to guide the geese away quietly",
        tags={"kindness", "animals"},
    ),
    "jump_fence": Method(
        id="jump_fence",
        label="jump fence",
        phrase="a quick fence jump",
        works_for={"thorn_patch", "mud_rut", "sleeping_geese"},
        kind=0,
        follow_rule=False,
        action="jumped the fence in a hurry",
        qa_text="jumped the fence",
        tags={"shortcut"},
    ),
}

GIRL_NAMES = ["Milly", "Daisy", "Poppy", "Lark", "Nell"]
BOY_NAMES = ["Toby", "Pip", "Robin", "Moss", "Wren"]
KINDS = [
    ("lamb", "lamb"),
    ("duck", "duck"),
    ("goose", "goose"),
    ("frog", "frog"),
]


@dataclass
class StoryParams:
    prize: str
    boundary: str
    method: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    parent: str
    shortcut: bool = True
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
    "north": [
        (
            "What does north mean?",
            "North is one direction on a place map. People use it to say where something is, like the north side of a garden.",
        )
    ],
    "constraint": [
        (
            "What is a constraint?",
            "A constraint is a limit or rule that tells what must not be done. A good constraint can keep people, plants, and animals safe.",
        )
    ],
    "thorn": [
        (
            "Why are thorns hard to walk through?",
            "Thorns are sharp parts of some plants. They can snag clothes and prick skin, so it is better to go around them.",
        )
    ],
    "mud": [
        (
            "Why can mud be troublesome?",
            "Mud is soft, wet earth. Feet can slip in it, and it can make clothes and shoes messy.",
        )
    ],
    "geese": [
        (
            "Why should you move quietly near sleeping geese?",
            "Sleeping geese can wake and feel startled if someone rushes close. Quiet steps are kinder and safer for both children and birds.",
        )
    ],
    "path": [
        (
            "Why is a path useful in a garden?",
            "A path gives people a safe place to walk. It also helps protect flowers and soft ground from being stepped on.",
        )
    ],
    "tool": [
        (
            "Why can a tool help instead of a shortcut?",
            "A good tool lets you solve the problem without rushing into danger. It helps you reach something safely while following the rules.",
        )
    ],
    "kindness": [
        (
            "What does kindness mean in a garden story?",
            "Kindness means thinking about others, not only yourself. It can mean protecting flowers, being gentle with animals, and listening to caring advice.",
        )
    ],
    "patience": [
        (
            "Why is patience a good moral?",
            "Patience helps you slow down and choose wisely. When you wait and think, small troubles often stay small.",
        )
    ],
    "bell": [
        (
            "What is a bell?",
            "A bell is a small object that rings when it moves. Its sound can be bright and cheerful.",
        )
    ],
    "hat": [
        (
            "What is a bonnet?",
            "A bonnet is a soft hat with a brim or ribbons. It helps cover the head and can blow away in the wind.",
        )
    ],
    "wind": [
        (
            "What does wind do to light things?",
            "Wind can push and carry light things, like ribbons, hats, and pinwheels. That is why they can drift away.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "north",
    "constraint",
    "thorn",
    "mud",
    "geese",
    "path",
    "tool",
    "kindness",
    "patience",
    "bell",
    "hat",
    "wind",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prize = f["prize"]
    boundary = f["boundary"]
    method = f["method"]
    return [
        (
            f'Write a nursery-rhyme-style moral story for a 3-to-5-year-old that uses '
            f'the words "north" and "constraint" and features a child who wants to get a {prize.label} back.'
        ),
        (
            f"Tell a gentle rhyming tale where {hero.id} sees a {prize.label} on the north side of the garden, "
            f"but {boundary.label} creates a real constraint, and patience leads to a kinder solution."
        ),
        (
            f"Write a short moral rhyme in which {friend.id} warns {hero.id} not to rush, "
            f"and a grown-up safely helps by using {method.phrase}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    prize = f["prize"]
    boundary = f["boundary"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about little {hero.id} and little {friend.id} in a garden, and {parent.label_word} who helps at the end.",
        ),
        (
            f"Where did the {prize.label} go?",
            f"It blew to the north side of the garden and came to rest near {boundary.phrase}. That made the children want it quickly, but the way there was not safe.",
        ),
        (
            f"Why did {friend.id} warn {hero.id}?",
            f"{friend.id} warned {hero.id} because {boundary.phrase} was a real constraint. Going straight through could cause trouble, so the warning came from care, not meanness.",
        ),
    ]
    if f["outcome"] == "trouble":
        if boundary.id == "thorn_patch":
            detail = f"{hero.id} got snagged by the thorn patch."
        elif boundary.id == "mud_rut":
            detail = f"{hero.id} slipped into the muddy rut."
        else:
            detail = f"The sleeping geese woke and frightened {hero.id}."
        qa.append(
            (
                f"What happened when {hero.id} tried the shortcut?",
                f"{detail} The trouble happened because {hero.pronoun('subject')} rushed past the warning instead of respecting the constraint.",
            )
        )
    else:
        qa.append(
            (
                f"What did {hero.id} do after the warning?",
                f"{hero.id} stopped and chose not to rush. That patient choice kept the problem small and made the safe solution easy.",
            )
        )
    qa.append(
        (
            f"How did {parent.label_word} help?",
            f"{parent.label_word.capitalize()} {method.qa_text}. The helper solved the problem without hurting flowers, waking animals, or sending {hero.id} into danger.",
        )
    )
    qa.append(
        (
            "What is the moral of the story?",
            f"The moral is to be patient and to listen to kind guidance. A good constraint may feel slow at first, but it protects both you and the world around you.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"north", "constraint"} | set(f["boundary"].tags) | set(f["method"].tags) | set(f["prize"].tags)
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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        prize="bell",
        boundary="thorn_patch",
        method="long_hook",
        hero_name="Milly",
        hero_type="lamb",
        friend_name="Pip",
        friend_type="duck",
        parent="mother",
        shortcut=True,
    ),
    StoryParams(
        prize="bonnet",
        boundary="mud_rut",
        method="garden_path",
        hero_name="Toby",
        hero_type="frog",
        friend_name="Daisy",
        friend_type="goose",
        parent="father",
        shortcut=True,
    ),
    StoryParams(
        prize="pinwheel",
        boundary="sleeping_geese",
        method="grain_bowl",
        hero_name="Poppy",
        hero_type="duck",
        friend_name="Robin",
        friend_type="frog",
        parent="mother",
        shortcut=False,
    ),
    StoryParams(
        prize="bell",
        boundary="sleeping_geese",
        method="garden_path",
        hero_name="Nell",
        hero_type="goose",
        friend_name="Wren",
        friend_type="lamb",
        parent="father",
        shortcut=False,
    ),
]


def explain_rejection(boundary: Boundary, method: Method) -> str:
    if not method_works(boundary, method):
        return (
            f"(No story: {method.label} does not actually solve the problem posed by {boundary.label}. "
            f"The fix must fit the obstacle.)"
        )
    if method.kind < KIND_MIN:
        return (
            f"(No story: method '{method.id}' is known but refused because it is not kind or careful enough. "
            f"This world prefers patient, moral solutions.)"
        )
    if not method.follow_rule:
        return (
            f"(No story: method '{method.id}' breaks the garden rule instead of respecting the constraint.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "trouble" if params.shortcut else "obedient"


ASP_RULES = r"""
works(B, M) :- solves(M, B).
kind(M) :- method(M), kind_score(M, S), kind_min(K), S >= K, follows_rule(M).

valid(P, B, M) :- prize(P), boundary(B), method(M), works(B, M), kind(M).

outcome(trouble) :- shortcut.
outcome(obedient) :- not shortcut.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for bid in BOUNDARIES:
        lines.append(asp.fact("boundary", bid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("kind_score", mid, method.kind))
        if method.follow_rule:
            lines.append(asp.fact("follows_rule", mid))
        for b in sorted(method.works_for):
            lines.append(asp.fact("solves", mid, b))
    lines.append(asp.fact("kind_min", KIND_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("shortcut") if params.shortcut else ""
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme moral story world: north wind, a garden constraint, and a patient fix."
    )
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--boundary", choices=BOUNDARIES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--shortcut", choices=["yes", "no"], help="whether the hero tries an impatient shortcut")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name_and_type(rng: random.Random, avoid_name: str = "") -> tuple[str, str]:
    name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != avoid_name])
    animal, typ = rng.choice(KINDS)
    return name, typ


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.boundary and args.method:
        boundary = BOUNDARIES[args.boundary]
        method = METHODS[args.method]
        if not (method_works(boundary, method) and is_kind(method)):
            raise StoryError(explain_rejection(boundary, method))
    if args.method and METHODS[args.method].kind < KIND_MIN:
        raise StoryError(explain_rejection(BOUNDARIES[args.boundary] if args.boundary else next(iter(BOUNDARIES.values())), METHODS[args.method]))
    if args.method and not METHODS[args.method].follow_rule:
        raise StoryError(explain_rejection(BOUNDARIES[args.boundary] if args.boundary else next(iter(BOUNDARIES.values())), METHODS[args.method]))

    combos = [
        c for c in valid_combos()
        if (args.prize is None or c[0] == args.prize)
        and (args.boundary is None or c[1] == args.boundary)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    prize_id, boundary_id, method_id = rng.choice(sorted(combos))
    hero_name, hero_type = _pick_name_and_type(rng)
    friend_name, friend_type = _pick_name_and_type(rng, avoid_name=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    shortcut = {"yes": True, "no": False}.get(args.shortcut, rng.choice([True, False]))
    return StoryParams(
        prize=prize_id,
        boundary=boundary_id,
        method=method_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        parent=parent,
        shortcut=shortcut,
    )


def generate(params: StoryParams) -> StorySample:
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.boundary not in BOUNDARIES:
        raise StoryError(f"(Unknown boundary: {params.boundary})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    boundary = BOUNDARIES[params.boundary]
    method = METHODS[params.method]
    if not method_works(boundary, method):
        raise StoryError(explain_rejection(boundary, method))
    if not is_kind(method):
        raise StoryError(explain_rejection(boundary, method))

    world = tell(
        prize=PRIZES[params.prize],
        boundary=boundary,
        method=method,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        parent_type=params.parent,
        shortcut=params.shortcut,
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
        print(f"{len(combos)} compatible (prize, boundary, method) combos:\n")
        for prize, boundary, method in combos:
            print(f"  {prize:8} {boundary:15} {method}")
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
                f"### {p.hero_name}: {p.prize} by {p.boundary} "
                f"({p.method}, {'shortcut' if p.shortcut else 'patient'})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
