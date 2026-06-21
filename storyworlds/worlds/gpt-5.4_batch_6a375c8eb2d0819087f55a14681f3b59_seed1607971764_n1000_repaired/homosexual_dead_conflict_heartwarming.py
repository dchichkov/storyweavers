#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/homosexual_dead_conflict_heartwarming.py
===================================================================

A standalone storyworld about a child with two dads who finds a dead small
creature during an outing. One dad wants to hurry away from the sad sight;
the other wants to stop and be kind. The conflict is gentle but real, and the
story resolves through a small memorial, an apology, and an ending image that
shows the family has slowed down and stayed tender.

Run it
------
    python storyworlds/worlds/gpt-5.4/homosexual_dead_conflict_heartwarming.py
    python storyworlds/worlds/gpt-5.4/homosexual_dead_conflict_heartwarming.py --place beach --creature crab --memorial sand_heart
    python storyworlds/worlds/gpt-5.4/homosexual_dead_conflict_heartwarming.py --place riverside --memorial flower_circle
    python storyworlds/worlds/gpt-5.4/homosexual_dead_conflict_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/homosexual_dead_conflict_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/homosexual_dead_conflict_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"father": "dad", "mother": "mom"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    path: str
    creatures: set[str] = field(default_factory=set)
    memorials: set[str] = field(default_factory=set)
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
class Creature:
    id: str
    label: str
    phrase: str
    spot: str
    tiny_detail: str
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
class Memorial:
    id: str
    label: str
    offer: str
    action: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_discovery_grief(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["dead"] < THRESHOLD:
        return []
    sig = ("discovery_grief", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    dad1 = world.get("dad1")
    dad2 = world.get("dad2")
    child.memes["sadness"] += 1
    dad1.memes["care"] += 1
    dad2.memes["care"] += 1
    return []


def _r_conflict_worry(world: World) -> list[str]:
    family = world.get("family")
    child = world.get("child")
    if family.meters["conflict"] < THRESHOLD or child.memes["sadness"] < THRESHOLD:
        return []
    sig = ("conflict_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return []


def _r_memorial_soothes(world: World) -> list[str]:
    ritual = world.get("ritual")
    if ritual.meters["done"] < THRESHOLD:
        return []
    sig = ("memorial_soothes",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    dad1 = world.get("dad1")
    dad2 = world.get("dad2")
    family = world.get("family")
    child.memes["sadness"] = max(0.0, child.memes["sadness"] - 0.5)
    child.memes["calm"] += 1
    child.memes["love"] += 1
    dad1.memes["love"] += 1
    dad2.memes["love"] += 1
    family.meters["closeness"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="discovery_grief", tag="emotion", apply=_r_discovery_grief),
    Rule(name="conflict_worry", tag="emotion", apply=_r_conflict_worry),
    Rule(name="memorial_soothes", tag="emotion", apply=_r_memorial_soothes),
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
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the community garden",
        opening="Rows of beans leaned on sticks, and marigolds nodded in the warm air.",
        path="the little dirt path by the flower beds",
        creatures={"sparrow", "butterfly"},
        memorials={"flower_circle", "stone_marker", "bury"},
        tags={"garden"},
    ),
    "park": Setting(
        id="park",
        place="the park",
        opening="The swings creaked softly, and clover shone bright beside the path.",
        path="the grass near the benches",
        creatures={"sparrow", "butterfly"},
        memorials={"flower_circle", "stone_marker", "bury"},
        tags={"park"},
    ),
    "riverside": Setting(
        id="riverside",
        place="the riverside walk",
        opening="The water made a shushing sound against the stones.",
        path="the smooth edge beside the water",
        creatures={"fish", "sparrow"},
        memorials={"leaf_boat", "stone_marker"},
        tags={"river"},
    ),
    "beach": Setting(
        id="beach",
        place="the beach",
        opening="The tide kept folding silver lines across the sand.",
        path="the damp sand above the foam",
        creatures={"crab", "sparrow"},
        memorials={"sand_heart", "stone_marker"},
        tags={"beach"},
    ),
}

CREATURES = {
    "sparrow": Creature(
        id="sparrow",
        label="sparrow",
        phrase="a small sparrow",
        spot="with one wing tucked under",
        tiny_detail="Its brown feathers looked as light as dry leaves.",
        tags={"bird", "dead"},
    ),
    "butterfly": Creature(
        id="butterfly",
        label="butterfly",
        phrase="a bright butterfly",
        spot="still beside a daisy stem",
        tiny_detail="Its folded wings looked like painted paper.",
        tags={"insect", "dead"},
    ),
    "fish": Creature(
        id="fish",
        label="fish",
        phrase="a silver fish",
        spot="caught between two stones",
        tiny_detail="Its scales gave one soft flash in the light.",
        tags={"fish", "dead"},
    ),
    "crab": Creature(
        id="crab",
        label="crab",
        phrase="a little crab",
        spot="lying near a ribbon of seaweed",
        tiny_detail="One small shell claw pointed at the sky.",
        tags={"crab", "dead"},
    ),
}

MEMORIALS = {
    "flower_circle": Memorial(
        id="flower_circle",
        label="flower circle",
        offer="make a little flower circle",
        action="They placed tiny blossoms in a soft ring and said goodbye in quiet voices.",
        ending_image="On the way home, the child kept one fallen petal in a pocket and walked more slowly than before.",
        tags={"flowers", "goodbye"},
    ),
    "stone_marker": Memorial(
        id="stone_marker",
        label="stone marker",
        offer="make a small stone marker",
        action="They set smooth stones beside it, one by one, until the small place looked cared for.",
        ending_image="On the way home, the child rolled a warm pebble in a palm and remembered that kindness could be small and real.",
        tags={"stones", "goodbye"},
    ),
    "leaf_boat": Memorial(
        id="leaf_boat",
        label="leaf boat",
        offer="send a leaf boat with a wish",
        action="They folded a broad leaf, set it on the water, and watched it carry their whispered wish downstream.",
        ending_image="On the way home, the child kept glancing at the river, as if the little leaf boat were still sailing kindly along.",
        tags={"river", "goodbye"},
    ),
    "sand_heart": Memorial(
        id="sand_heart",
        label="sand heart",
        offer="draw a heart in the sand",
        action="They drew a careful heart nearby and let the sea breeze smooth their voices into something gentle.",
        ending_image="On the way home, the child looked back once at the heart in the sand and squeezed both dads' hands.",
        tags={"beach", "goodbye"},
    ),
    "bury": Memorial(
        id="bury",
        label="tiny burial",
        offer="make a tiny burial place",
        action="They scooped a little hollow in the soft ground, covered it gently, and patted the earth flat together.",
        ending_image="On the way home, the child turned once toward the small patch of earth and felt less alone in the sadness.",
        tags={"soil", "goodbye"},
    ),
}


@dataclass
class StoryParams:
    place: str
    creature: str
    memorial: str
    child_name: str
    child_gender: str
    dad1_name: str
    dad2_name: str
    hasty_dad: str
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


GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ella", "Ivy", "Ruby", "Anna"]
BOY_NAMES = ["Milo", "Theo", "Sam", "Eli", "Noah", "Ben", "Finn", "Leo"]
DAD_NAMES = ["Jon", "Luis", "Marco", "Evan", "Rafi", "Omar", "David", "Paul"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for creature_id in sorted(setting.creatures):
            for memorial_id in sorted(setting.memorials):
                combos.append((place_id, creature_id, memorial_id))
    return combos


def explain_rejection(place: Setting, creature: Creature, memorial: Memorial) -> str:
    if creature.id not in place.creatures:
        return (
            f"(No story: {creature.phrase} is not a good fit for {place.place}. "
            f"Pick a creature this setting can reasonably contain.)"
        )
    return (
        f"(No story: a {memorial.label} does not fit {place.place}. "
        f"Choose a memorial the place can honestly support.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "shared_memorial"


ASP_RULES = r"""
valid(P,C,M) :- setting(P), creature(C), memorial(M),
                affords_creature(P,C), affords_memorial(P,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for creature_id in sorted(setting.creatures):
            lines.append(asp.fact("affords_creature", place_id, creature_id))
        for memorial_id in sorted(setting.memorials):
            lines.append(asp.fact("affords_memorial", place_id, memorial_id))
    for creature_id in CREATURES:
        lines.append(asp.fact("creature", creature_id))
    for memorial_id in MEMORIALS:
        lines.append(asp.fact("memorial", memorial_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def introduce_family(world: World, child: Entity, dad1: Entity, dad2: Entity) -> None:
    world.say(
        f"{child.id} was out for a walk with {dad1.id} and {dad2.id}. "
        f"{child.id} did not use the long word homosexual very often, but "
        f"{child.pronoun()} knew it meant {dad1.id} and {dad2.id} loved each other "
        f"and had made a family together."
    )
    world.say(world.setting.opening)


def stroll(world: World, child: Entity, dad1: Entity, dad2: Entity) -> None:
    child.memes["contentment"] += 1
    dad1.memes["contentment"] += 1
    dad2.memes["contentment"] += 1
    world.say(
        f"They walked along {world.setting.path}, with {child.id} skipping between "
        f"{dad1.id} and {dad2.id}."
    )


def discover(world: World, child: Entity, creature_cfg: Creature) -> None:
    creature = world.get("creature")
    creature.meters["dead"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} stopped. There, on {world.setting.path}, was {creature_cfg.phrase}, "
        f"{creature_cfg.spot}. It was dead."
    )
    world.say(creature_cfg.tiny_detail)
    world.say(f'{child.id} whispered, "Oh."')


def disagree(world: World, child: Entity, hasty: Entity, steady: Entity, memorial: Memorial) -> None:
    family = world.get("family")
    family.meters["conflict"] = 1.0
    hasty.memes["hurry"] += 1
    steady.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Come on," {hasty.id} said softly. "Let\'s keep moving."'
    )
    world.say(
        f'But {steady.id} shook {steady.pronoun("possessive")} head. '
        f'"Maybe we should stop for a minute. We could {memorial.offer}."'
    )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.id} looked from one dad to the other. The arguing felt too loud "
            f"next to something so still."
        )


def child_turn(world: World, child: Entity, hasty: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'Taking a small breath, {child.id} said, "Please don\'t fight. '
        f'I don\'t want it to be alone."'
    )
    hasty.memes["shame"] += 1


def repair(world: World, child: Entity, hasty: Entity, steady: Entity) -> None:
    family = world.get("family")
    family.meters["conflict"] = 0.0
    family.meters["repair"] = 1.0
    hasty.memes["hurry"] = 0.0
    hasty.memes["care"] += 1
    hasty.memes["love"] += 1
    steady.memes["love"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"{hasty.id} looked at {child.id}'s face and let out a slow breath. "
        f'"You are right," {hasty.pronoun()} said. "I was trying to hurry past the sad part. '
        f'I am sorry."'
    )
    world.say(
        f"{steady.id} touched {hasty.id}'s sleeve, and the sharp little moment between them softened."
    )


def perform_memorial(world: World, child: Entity, dad1: Entity, dad2: Entity, memorial: Memorial) -> None:
    ritual = world.get("ritual")
    ritual.meters["done"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"So the three of them knelt down together. {memorial.action}"
    )
    world.say(
        f'{dad2.id if dad2.memes["care"] >= dad1.memes["care"] else dad1.id} said, '
        f'"Goodbye, little one," and {child.id} echoed the words.'
    )


def walk_home(world: World, child: Entity, dad1: Entity, dad2: Entity, memorial: Memorial) -> None:
    child.memes["safety"] += 1
    dad1.memes["safety"] += 1
    dad2.memes["safety"] += 1
    world.say(
        f"When they stood up again, nobody was rushing anymore. "
        f"{child.id} took one hand from each dad, and they started home together."
    )
    world.say(memorial.ending_image)


def tell(
    setting: Setting,
    creature_cfg: Creature,
    memorial: Memorial,
    child_name: str = "Milo",
    child_gender: str = "boy",
    dad1_name: str = "Jon",
    dad2_name: str = "Luis",
    hasty_dad: str = "dad1",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    dad1 = world.add(Entity(id=dad1_name, kind="character", type="father", role="dad1"))
    dad2 = world.add(Entity(id=dad2_name, kind="character", type="father", role="dad2"))
    creature = world.add(Entity(id="creature", kind="thing", type=creature_cfg.id, label=creature_cfg.label))
    ritual = world.add(Entity(id="ritual", kind="thing", type="memorial", label=memorial.label))
    family = world.add(Entity(id="family", kind="thing", type="family", label="the family"))

    child.attrs["home"] = "two_dads"
    dad1.attrs["partner"] = dad2.id
    dad2.attrs["partner"] = dad1.id
    family.attrs["setting"] = setting.id
    family.attrs["hasty_dad"] = hasty_dad
    world.facts["homosexual_family"] = True

    introduce_family(world, child, dad1, dad2)
    stroll(world, child, dad1, dad2)

    world.para()
    discover(world, child, creature_cfg)

    hasty = dad1 if hasty_dad == "dad1" else dad2
    steady = dad2 if hasty_dad == "dad1" else dad1

    disagree(world, child, hasty, steady, memorial)

    world.para()
    child_turn(world, child, hasty)
    repair(world, child, hasty, steady)
    perform_memorial(world, child, dad1, dad2, memorial)
    walk_home(world, child, dad1, dad2, memorial)

    world.facts.update(
        child=child,
        dad1=dad1,
        dad2=dad2,
        hasty=hasty,
        steady=steady,
        creature_cfg=creature_cfg,
        creature=creature,
        memorial=memorial,
        setting=setting,
        conflict=True,
        repaired=family.meters["repair"] >= THRESHOLD,
        sadness=child.memes["sadness"],
        calm=child.memes["calm"],
    )
    return world


KNOWLEDGE = {
    "homosexual": [
        (
            "What does homosexual mean?",
            "Homosexual is a word for a person who loves someone of the same sex. In this story, it means the child has two dads who love each other and care for the family together.",
        )
    ],
    "dead": [
        (
            "What does dead mean?",
            "Dead means a living thing's body has stopped working and it cannot come back to life. That is why the family speaks gently and says goodbye.",
        )
    ],
    "grief": [
        (
            "Why can saying goodbye help when something dies?",
            "A small goodbye can help people share sadness instead of carrying it alone. Kind actions do not change the loss, but they can make hearts feel less lonely.",
        )
    ],
    "bird": [
        (
            "What is a sparrow?",
            "A sparrow is a small bird with short hops and quick wings. You often see sparrows near gardens and parks.",
        )
    ],
    "insect": [
        (
            "What is a butterfly?",
            "A butterfly is an insect with large wings covered in tiny colored scales. It starts life as a caterpillar and changes as it grows.",
        )
    ],
    "fish": [
        (
            "Why do fish need water?",
            "Fish live in water and use their gills to take oxygen from it. Out of water, their bodies cannot work the way they should.",
        )
    ],
    "crab": [
        (
            "What is a crab?",
            "A crab is a sea animal with a hard shell and sideways walk. Many crabs live near beaches and rocks.",
        )
    ],
    "flowers": [
        (
            "Why do people use flowers when saying goodbye?",
            "Flowers are soft, beautiful, and easy to place gently. People often use them to show care and love.",
        )
    ],
    "stones": [
        (
            "Why can a little stone marker feel special?",
            "A stone marker shows that someone stopped, noticed, and cared. Even a small row of stones can say, 'You mattered.'",
        )
    ],
    "river": [
        (
            "What is a river?",
            "A river is water that keeps moving across the land. It can carry leaves, sticks, and little boats downstream.",
        )
    ],
    "beach": [
        (
            "What does the tide do at the beach?",
            "The tide makes the sea move in and out over the shore. That is why lines in the sand can change through the day.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "homosexual",
    "dead",
    "grief",
    "bird",
    "insect",
    "fish",
    "crab",
    "flowers",
    "stones",
    "river",
    "beach",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    creature_cfg = f["creature_cfg"]
    memorial = f["memorial"]
    setting = f["setting"]
    hasty = f["hasty"]
    steady = f["steady"]
    return [
        (
            f'Write a heartwarming story for a young child that includes the words '
            f'"homosexual" and "dead", where a child with two dads finds {creature_cfg.phrase} '
            f'at {setting.place} and the family has a gentle conflict before making peace.'
        ),
        (
            f"Tell a warm family story where {hasty.id} wants to hurry past something sad, "
            f"but {steady.id} suggests they {memorial.offer}, and {child.id} helps the grown-ups listen better."
        ),
        (
            f"Write a simple story about grief and kindness in which a child sees a dead {creature_cfg.label}, "
            f"speaks honestly, and goes home holding both dads' hands."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    dad1 = f["dad1"]
    dad2 = f["dad2"]
    hasty = f["hasty"]
    steady = f["steady"]
    creature_cfg = f["creature_cfg"]
    memorial = f["memorial"]
    setting = f["setting"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} two dads, {dad1.id} and {dad2.id}. They are a loving family taking a walk together.",
        ),
        (
            f"What did {child.id} find?",
            f"{child.id} found {creature_cfg.phrase} at {setting.place}. It was dead, which is why the mood changed so quickly from calm to sad.",
        ),
        (
            "What was the conflict?",
            f"{hasty.id} wanted to keep walking, but {steady.id} wanted the family to pause and show kindness. The disagreement mattered because {child.id} was already sad and did not want the little creature left alone.",
        ),
        (
            f"How did {child.id} help fix the problem?",
            f"{child.id} spoke up and asked the grown-ups not to fight. That honest little sentence helped {hasty.id} notice that rushing was hurting more than helping.",
        ),
        (
            "How did the family say goodbye?",
            f"They chose a {memorial.label}. Doing one gentle action together turned the argument into care and helped the family feel close again.",
        ),
        (
            "How did the story end?",
            f"It ended with the family walking home hand in hand and no one rushing anymore. The ending image shows that they had changed from a tense, hurried family moment into a softer, more loving one.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"homosexual", "dead", "grief"}
    tags |= set(world.facts["creature_cfg"].tags)
    tags |= set(world.facts["memorial"].tags)
    tags |= set(world.facts["setting"].tags)
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


CURATED = [
    StoryParams(
        place="park",
        creature="sparrow",
        memorial="flower_circle",
        child_name="Milo",
        child_gender="boy",
        dad1_name="Jon",
        dad2_name="Luis",
        hasty_dad="dad1",
    ),
    StoryParams(
        place="garden",
        creature="butterfly",
        memorial="bury",
        child_name="Lina",
        child_gender="girl",
        dad1_name="Marco",
        dad2_name="Evan",
        hasty_dad="dad2",
    ),
    StoryParams(
        place="riverside",
        creature="fish",
        memorial="leaf_boat",
        child_name="Theo",
        child_gender="boy",
        dad1_name="Rafi",
        dad2_name="Omar",
        hasty_dad="dad1",
    ),
    StoryParams(
        place="beach",
        creature="crab",
        memorial="sand_heart",
        child_name="Ruby",
        child_gender="girl",
        dad1_name="David",
        dad2_name="Paul",
        hasty_dad="dad2",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, two dads, a sad discovery, a gentle conflict, and a heartwarming goodbye."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--memorial", choices=MEMORIALS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--dad1-name")
    ap.add_argument("--dad2-name")
    ap.add_argument("--hasty-dad", choices=["dad1", "dad2"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches the Python gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _pick_two_dads(rng: random.Random) -> tuple[str, str]:
    dad1, dad2 = rng.sample(DAD_NAMES, 2)
    return dad1, dad2


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creature and args.memorial:
        setting = SETTINGS[args.place]
        creature_cfg = CREATURES[args.creature]
        memorial = MEMORIALS[args.memorial]
        if (args.place, args.creature, args.memorial) not in valid_combos():
            raise StoryError(explain_rejection(setting, creature_cfg, memorial))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.memorial is None or combo[2] == args.memorial)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, creature, memorial = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_child_name(rng, gender)
    dad1_name = args.dad1_name
    dad2_name = args.dad2_name
    if dad1_name and dad2_name and dad1_name == dad2_name:
        raise StoryError("(No story: the two dads need different names so the story stays clear.)")
    if dad1_name is None or dad2_name is None:
        d1, d2 = _pick_two_dads(rng)
        dad1_name = dad1_name or d1
        dad2_name = dad2_name or (d2 if d2 != dad1_name else rng.choice([n for n in DAD_NAMES if n != dad1_name]))
    hasty_dad = args.hasty_dad or rng.choice(["dad1", "dad2"])

    return StoryParams(
        place=place,
        creature=creature,
        memorial=memorial,
        child_name=child_name,
        child_gender=gender,
        dad1_name=dad1_name,
        dad2_name=dad2_name,
        hasty_dad=hasty_dad,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.creature not in CREATURES:
        raise StoryError(f"(No story: unknown creature '{params.creature}'.)")
    if params.memorial not in MEMORIALS:
        raise StoryError(f"(No story: unknown memorial '{params.memorial}'.)")
    if (params.place, params.creature, params.memorial) not in valid_combos():
        raise StoryError(
            explain_rejection(SETTINGS[params.place], CREATURES[params.creature], MEMORIALS[params.memorial])
        )
    if params.hasty_dad not in {"dad1", "dad2"}:
        raise StoryError("(No story: hasty dad must be dad1 or dad2.)")
    if params.dad1_name == params.dad2_name:
        raise StoryError("(No story: the two dads need different names.)")

    world = tell(
        setting=SETTINGS[params.place],
        creature_cfg=CREATURES[params.creature],
        memorial=MEMORIALS[params.memorial],
        child_name=params.child_name,
        child_gender=params.child_gender,
        dad1_name=params.dad1_name,
        dad2_name=params.dad2_name,
        hasty_dad=params.hasty_dad,
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=False, header="")
        finally:
            sys.stdout = old_stdout
        if not buf.getvalue().strip():
            raise StoryError("emit produced no text")
        print("OK: smoke-tested ordinary generate()/emit().")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in CURATED:
        try:
            sample = generate(params)
            if "homosexual" not in sample.story or "dead" not in sample.story:
                raise StoryError("required seed words missing from story text")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
            break
    else:
        print(f"OK: generated {len(CURATED)} curated stories.")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creature, memorial) combos:\n")
        for place, creature, memorial in combos:
            print(f"  {place:10} {creature:10} {memorial}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.creature} at {p.place} ({p.memorial})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
