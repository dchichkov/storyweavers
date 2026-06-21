#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py
=====================================================================

A standalone story world for a small fairy-tale domain: a young fairy leaves
home on a quest to fetch a magical blessing for a fading tree, uses the right
helper to cross one true obstacle, and comes home changed. The ending is not
just a reward scene; the world model makes the tree bloom first, and that brave,
generous act empowers the hero's transformation.

Run it
------
    python storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py --source moonwell --helper lantern
    python storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py --source starlake --helper lantern
    python storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py --json
    python storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py --asp
    python storyworlds/worlds/gpt-5.4/empower_quest_transformation_fairy_tale.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy_girl", "queen", "mother", "grandmother", "woman"}
        male = {"boy", "fairy_boy", "king", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "grandmother":
            return "grandmother"
        if self.type == "grandfather":
            return "grandfather"
        return self.label or self.type


@dataclass
class Source:
    id: str
    label: str
    place: str
    obstacle: str
    need: str
    blessing: str
    vessel: str
    approach: str
    obstacle_line: str
    collect_line: str
    return_line: str
    bloom_line: str
    wing_color: str
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
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    use_line: str = ""
    qa_line: str = ""
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


def _r_tree_sadness(world: World) -> list[str]:
    tree = world.get("tree")
    hero = world.get("hero")
    village = world.get("village")
    if tree.meters["glow"] >= THRESHOLD:
        return []
    sig = ("tree_sadness",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["concern"] += 1
    village.memes["worry"] += 1
    return []


def _r_crossing(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.meters["on_quest"] < THRESHOLD or hero.meters["past_obstacle"] >= THRESHOLD:
        return []
    need = world.facts["source"].need
    sig = ("crossing", need, helper.id)
    if sig in world.fired:
        return []
    if need in helper.attrs.get("solves", set()):
        world.fired.add(sig)
        hero.meters["past_obstacle"] += 1
        hero.meters["progress"] += 1
        hero.memes["courage"] += 1
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    return []


def _r_collect(world: World) -> list[str]:
    hero = world.get("hero")
    source_ent = world.get("source")
    if hero.meters["past_obstacle"] < THRESHOLD or hero.meters["has_blessing"] >= THRESHOLD:
        return []
    sig = ("collect", source_ent.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["has_blessing"] += 1
    hero.meters["progress"] += 1
    source_ent.meters["shared"] += 1
    hero.memes["hope"] += 1
    return []


def _r_heal(world: World) -> list[str]:
    hero = world.get("hero")
    tree = world.get("tree")
    village = world.get("village")
    if hero.meters["has_blessing"] < THRESHOLD or hero.meters["at_home"] < THRESHOLD:
        return []
    if tree.meters["bloom"] >= THRESHOLD:
        return []
    sig = ("heal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tree.meters["glow"] += 2
    tree.meters["bloom"] += 1
    village.memes["hope"] += 1
    hero.memes["joy"] += 1
    hero.memes["generous"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    hero = world.get("hero")
    tree = world.get("tree")
    if tree.meters["bloom"] < THRESHOLD or hero.meters["transformed"] >= THRESHOLD:
        return []
    if hero.memes["courage"] < THRESHOLD or hero.memes["generous"] < THRESHOLD:
        return []
    sig = ("transform", world.facts["source"].wing_color)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["transformed"] += 1
    hero.meters["wing_glow"] += 1
    hero.memes["empowered"] += 1
    hero.attrs["wing_color"] = world.facts["source"].wing_color
    return []


CAUSAL_RULES = [
    Rule(name="tree_sadness", tag="emotional", apply=_r_tree_sadness),
    Rule(name="crossing", tag="quest", apply=_r_crossing),
    Rule(name="collect", tag="quest", apply=_r_collect),
    Rule(name="heal", tag="physical", apply=_r_heal),
    Rule(name="transform", tag="magical", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = changed or False
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def helper_fits(source: Source, helper: Helper) -> bool:
    return source.need in helper.solves


def transformation_of(source: Source) -> str:
    return source.wing_color


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for source_id, source in SOURCES.items():
        for helper_id, helper in HELPERS.items():
            if helper_fits(source, helper):
                combos.append((source_id, helper_id))
    return sorted(combos)


def explain_rejection(source: Source, helper: Helper) -> str:
    return (
        f"(No story: {helper.phrase} cannot solve the quest to {source.label}. "
        f"The road there needs help for {source.obstacle.replace('_', ' ')}, "
        f"so choose a helper meant for that obstacle.)"
    )


def outcome_of(params: "StoryParams") -> str:
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    source = SOURCES[params.source]
    helper = HELPERS[params.helper]
    if not helper_fits(source, helper):
        raise StoryError(explain_rejection(source, helper))
    return transformation_of(source)


def introduce(world: World, hero: Entity, elder: Entity, tree: Entity) -> None:
    world.say(
        f"In a small valley where dew pearls hung on every fern, there lived {hero.id}, "
        f"a young fairy with wings as pale as moth dust."
    )
    world.say(
        f"At the center of the valley stood {tree.phrase}. Once it had lit every doorstep "
        f"with soft gold, but now its branches drooped and only one sleepy glow remained."
    )
    world.say(
        f"{hero.id} loved the valley dearly, and when {hero.pronoun()} saw the dim tree, "
        f"{hero.pronoun()} pressed {hero.pronoun('possessive')} hands together and wished "
        f"{hero.pronoun()} were strong enough to help."
    )
    world.say(
        f"{elder.label_word.capitalize()} laid a gentle hand on {hero.pronoun('possessive')} "
        f"shoulder and said, \"There is one true cure. You must go on a quest and bring back "
        f"{world.facts['source'].blessing} from {world.facts['source'].label}.\""
    )


def give_helper(world: World, hero: Entity, elder: Entity, helper_ent: Entity, helper: Helper) -> None:
    hero.attrs["helper_name"] = helper.label
    world.say(
        f"Then {elder.label_word} opened a carved box and gave {hero.id} {helper.phrase}. "
        f"\"Take this,\" {elder.pronoun()} said. \"It will help you when the road grows hard.\""
    )


def set_out(world: World, hero: Entity, source: Source) -> None:
    hero.meters["on_quest"] += 1
    hero.memes["fear"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"So before the sun was high, {hero.id} set out toward {source.place}. "
        f"{source.approach}"
    )


def face_obstacle(world: World, hero: Entity, source: Source, helper: Helper) -> None:
    world.say(source.obstacle_line)
    if helper_fits(source, helper):
        world.say(helper.use_line)
    propagate(world, narrate=False)
    hero.attrs["used_helper"] = helper.id
    hero.attrs["crossed_obstacle"] = True


def collect_blessing(world: World, hero: Entity, source: Source) -> None:
    propagate(world, narrate=False)
    vessel = source.vessel
    world.say(source.collect_line.format(name=hero.id, vessel=vessel, blessing=source.blessing))
    hero.attrs["blessing_name"] = source.blessing


def return_home(world: World, hero: Entity, source: Source) -> None:
    hero.meters["at_home"] += 1
    hero.meters["on_quest"] = 0.0
    world.say(source.return_line.format(name=hero.id, blessing=source.blessing))


def heal_tree(world: World, hero: Entity, tree: Entity, source: Source) -> None:
    propagate(world, narrate=False)
    world.say(source.bloom_line)
    if world.get("tree").meters["bloom"] >= THRESHOLD:
        world.say(
            f"Warm light ran from branch to branch, and the little houses in the valley "
            f"shone as if evening had been stitched with stars."
        )


def transform_hero(world: World, hero: Entity, source: Source) -> None:
    propagate(world, narrate=False)
    if hero.meters["transformed"] >= THRESHOLD:
        world.say(
            f"As {hero.id} watched the valley brighten, a hush fell over the grass. "
            f"The brave journey and the kind gift seemed to empower {hero.pronoun('object')}. "
            f"{hero.pronoun('Possessive') if False else hero.pronoun('possessive').capitalize()} pale wings "
            f"flashed, and in a shimmer they turned {source.wing_color}."
        )
        world.say(
            f"From that day on, {hero.id} no longer felt like the smallest fairy in the valley. "
            f"{hero.pronoun().capitalize()} had become a bright guardian of the glowing tree."
        )


def ending_image(world: World, hero: Entity, elder: Entity, helper: Helper) -> None:
    tree = world.get("tree")
    if tree.meters["bloom"] >= THRESHOLD:
        world.say(
            f"That night, {elder.label_word} hung flower lanterns on the lowest bough, "
            f"and every child in the valley danced beneath the leaves."
        )
    world.say(
        f"When the moon rose, {hero.id} flew one small circle over the silver roofs, "
        f"{helper.label} tucked close, and the valley below looked safe, awake, and full of wonder."
    )


def tell(
    source: Source,
    helper: Helper,
    hero_name: str = "Mira",
    hero_type: str = "fairy_girl",
    elder_type: str = "grandmother",
    elder_name: str = "Grandmother",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["young", "gentle", "brave"],
        attrs={"wing_color": "pale", "helper_name": "", "blessing_name": "", "used_helper": ""},
        tags={"fairy", "quest"},
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_type,
        label=elder_name.lower(),
        role="elder",
        traits=["wise"],
        attrs={},
        tags={"elder"},
    ))
    tree = world.add(Entity(
        id="tree",
        kind="thing",
        type="tree",
        label="the heart tree",
        phrase="the Heart Tree",
        role="tree",
        attrs={},
        tags={"tree", "magic"},
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label="the valley",
        phrase="the valley",
        role="village",
        attrs={},
        tags={"village"},
    ))
    source_ent = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source.label,
        phrase=source.label,
        role="source",
        attrs={},
        tags=set(source.tags),
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="thing",
        type="helper",
        label=helper.label,
        phrase=helper.phrase,
        role="helper",
        attrs={"solves": set(helper.solves)},
        tags=set(helper.tags),
    ))

    tree.meters["glow"] = 0.0
    tree.meters["bloom"] = 0.0
    village.memes["hope"] = 0.0
    village.memes["worry"] = 0.0
    hero.meters["on_quest"] = 0.0
    hero.meters["past_obstacle"] = 0.0
    hero.meters["has_blessing"] = 0.0
    hero.meters["at_home"] = 0.0
    hero.meters["transformed"] = 0.0
    hero.meters["wing_glow"] = 0.0
    hero.meters["progress"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["courage"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["generous"] = 0.0
    hero.memes["empowered"] = 0.0
    hero.memes["concern"] = 0.0

    world.facts.update(
        source=source,
        helper=helper,
        hero=hero,
        elder=elder,
        tree=tree,
        village=village,
        transformation=source.wing_color,
        blessing=source.blessing,
        obstacle=source.obstacle,
        helper_used=helper.label,
    )
    propagate(world, narrate=False)

    introduce(world, hero, elder, tree)
    give_helper(world, hero, elder, helper_ent, helper)

    world.para()
    set_out(world, hero, source)
    face_obstacle(world, hero, source, helper)

    world.para()
    collect_blessing(world, hero, source)
    return_home(world, hero, source)

    world.para()
    heal_tree(world, hero, tree, source)
    transform_hero(world, hero, source)
    ending_image(world, hero, elder, helper)

    world.facts.update(
        quest_complete=hero.meters["has_blessing"] >= THRESHOLD and tree.meters["bloom"] >= THRESHOLD,
        transformed=hero.meters["transformed"] >= THRESHOLD,
        tree_bloomed=tree.meters["bloom"] >= THRESHOLD,
        wing_color=hero.attrs.get("wing_color", "pale"),
    )
    return world


SOURCES = {
    "moonwell": Source(
        id="moonwell",
        label="the Moonwell",
        place="the silver cave under the hill",
        obstacle="dark_path",
        need="dark_path",
        blessing="a cup of moonwater",
        vessel="an acorn cup",
        approach="The path wound under roots and stones until the daylight thinned to a silver thread.",
        obstacle_line="Soon the cave mouth opened before her, and inside it the dark was so deep that even brave thoughts seemed to whisper.",
        collect_line="{name} lifted {vessel} into the still pool, and the moonwater rose shining as if a star had melted into it.",
        return_line="Holding {blessing} carefully, {name} hurried home before a single bright drop could spill.",
        bloom_line="At the foot of the Heart Tree, the fairy poured the moonwater onto the roots. The bark drank it in, and pearl-white blossoms opened all at once.",
        wing_color="silver-blue",
        tags={"moonwell", "water", "cave", "quest"},
    ),
    "sunpool": Source(
        id="sunpool",
        label="the Sunpool",
        place="the hill of morning bells",
        obstacle="cold_wind",
        need="cold_wind",
        blessing="a cup of sunwater",
        vessel="a little shell bowl",
        approach="The path climbed higher and higher until the grass bent flat beneath the singing wind.",
        obstacle_line="Near the top, the wind pushed so hard that it tugged at her sleeves and tried to turn her around.",
        collect_line="{name} knelt by the golden pool and filled {vessel} with sunwater that glowed warm as honey.",
        return_line="With {blessing} cradled close, {name} came down the hill while the bell flowers nodded on both sides of the path.",
        bloom_line="At the foot of the Heart Tree, the fairy poured the sunwater over the roots. Golden buds swelled and burst into bright bells of bloom.",
        wing_color="golden-rose",
        tags={"sunpool", "water", "hill", "quest"},
    ),
    "starlake": Source(
        id="starlake",
        label="the Starlake",
        place="the reed marsh beyond the willow field",
        obstacle="bog_crossing",
        need="bog_crossing",
        blessing="a jar of starlight water",
        vessel="a glass jar",
        approach="The path ran past willow shadows until the ground grew soft and the reeds began to whisper together.",
        obstacle_line="At the marsh edge, black water spread in little pools, and there was no safe place for small feet to step.",
        collect_line="{name} dipped {vessel} into the quiet lake, and starlight water swirled inside it like a tiny night sky.",
        return_line="Carrying {blessing} with both hands, {name} crossed back through the reeds and did not stop until home lights winked ahead.",
        bloom_line="At the foot of the Heart Tree, the fairy poured the starlight water over the roots. Violet sparks ran up the trunk, and starry blossoms trembled open.",
        wing_color="violet-silver",
        tags={"starlake", "water", "marsh", "quest"},
    ),
}

HELPERS = {
    "lantern": Helper(
        id="lantern",
        label="lantern",
        phrase="a moon-lantern no bigger than an apple",
        solves={"dark_path"},
        use_line="She lifted the moon-lantern, and its round light floated ahead of her until the cave walls gleamed and the safe stones shone clear.",
        qa_line="The lantern made light in the cave, so she could see the safe way forward.",
        tags={"lantern", "light"},
    ),
    "glow_moss": Helper(
        id="glow_moss",
        label="glow moss",
        phrase="a twist of glow moss wrapped in silver thread",
        solves={"dark_path"},
        use_line="She unwound the glow moss, and a green-gold light spilled over the cave floor, showing her where to step.",
        qa_line="The glow moss shone in the dark cave and showed her the path.",
        tags={"glow_moss", "light"},
    ),
    "cloak": Helper(
        id="cloak",
        label="cloak",
        phrase="a red wool cloak with a clasp shaped like a leaf",
        solves={"cold_wind"},
        use_line="She fastened the red cloak at her throat, and the hard wind slid around her instead of knocking her back.",
        qa_line="The warm cloak shielded her from the strong wind on the hill.",
        tags={"cloak", "warmth"},
    ),
    "song_scarf": Helper(
        id="song_scarf",
        label="song scarf",
        phrase="a singing scarf woven from thistle silk",
        solves={"cold_wind"},
        use_line="She wrapped on the singing scarf, and its soft humming steadied her while the wind rushed past.",
        qa_line="The humming scarf helped her stay steady in the wind.",
        tags={"scarf", "warmth"},
    ),
    "rush_boat": Helper(
        id="rush_boat",
        label="rush boat",
        phrase="a tiny rush boat sealed with beeswax",
        solves={"bog_crossing"},
        use_line="She set the rush boat on the marsh water, stepped in, and drifted across the dark pools as lightly as a petal.",
        qa_line="The little boat carried her over the marsh water where she could not safely walk.",
        tags={"boat", "marsh"},
    ),
    "stepping_stones": Helper(
        id="stepping_stones",
        label="stepping stones",
        phrase="three flat stepping stones in a satchel of nettle cloth",
        solves={"bog_crossing"},
        use_line="One by one she laid down the stepping stones, making a safe little road over the soft marsh.",
        qa_line="The stones made a safe path across the marsh.",
        tags={"stones", "marsh"},
    ),
}

GIRL_NAMES = ["Mira", "Elin", "Tavi", "Nessa", "Luma", "Orla", "Suri", "Faye"]
BOY_NAMES = ["Rowan", "Ivo", "Tarin", "Pip", "Bram", "Lior", "Ari", "Nico"]


@dataclass
class StoryParams:
    source: str
    helper: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with an important goal. In fairy tales, a hero often goes on a quest to help someone or save something precious.",
        )
    ],
    "empower": [
        (
            "What does empower mean?",
            "To empower someone is to help them feel strong and able to act. It can also mean giving them what they need to do a hard thing well.",
        )
    ],
    "tree": [
        (
            "Why do fairy tales often use a special tree?",
            "A special tree can stand for the life of a whole place. When the tree grows strong, it shows that hope and peace have come back.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light carried from place to place. It helps you see in the dark.",
        )
    ],
    "cloak": [
        (
            "What does a cloak do?",
            "A cloak is a loose outer covering that can keep a traveler warm. In fairy tales, it can also make a hard road easier to bear.",
        )
    ],
    "boat": [
        (
            "Why use a small boat in a marsh?",
            "A marsh can be too soft or wet to walk across safely. A boat lets you travel over the water instead of sinking into it.",
        )
    ],
    "transformation": [
        (
            "What is a transformation in a fairy tale?",
            "A transformation is a deep change, like when someone becomes brighter, wiser, or takes on a new magical form. It often shows what the hero learned through the story.",
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "empower", "tree", "lantern", "cloak", "boat", "transformation"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    source = world.facts["source"]
    helper = world.facts["helper"]
    return [
        'Write a short fairy tale that includes the word "empower" and tells of a quest that leads to a transformation.',
        f"Tell a gentle fairy story where {hero.id}, a young fairy, travels to {source.label} with {helper.phrase} to save a fading magical tree.",
        f"Write a child-facing fairy tale in which bravery and kindness empower a small hero, and the ending shows the hero transformed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    source = world.facts["source"]
    helper = world.facts["helper"]
    tree = world.facts["tree"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young fairy, and {elder.label_word}, who sends {hero.pronoun('object')} on a quest. The quest matters because {tree.phrase} is fading and the whole valley needs its light.",
        ),
        (
            f"Why did {hero.id} leave home?",
            f"{hero.id} left home to fetch {source.blessing} from {source.label}. {elder.label_word.capitalize()} told {hero.pronoun('object')} it was the one true cure for the dim Heart Tree.",
        ),
        (
            f"How did {helper.label} help on the journey?",
            f"{helper.qa_line} That mattered because the road to {source.label} could not be crossed safely without the right kind of help.",
        ),
        (
            f"What changed when {hero.id} came back?",
            f"When {hero.id} poured {source.blessing} onto the roots, the Heart Tree bloomed again and the valley filled with light. Then the brave, generous deed seemed to empower {hero.pronoun('object')}, and {hero.pronoun('possessive')} wings turned {world.facts['wing_color']}.",
        ),
    ]
    if world.facts.get("transformed"):
        qa.append(
            (
                "What was the transformation in the story?",
                f"The transformation was in {hero.id}. After finishing the quest and helping the valley first, {hero.pronoun('possessive')} pale wings changed into {world.facts['wing_color']} wings, showing that {hero.pronoun()} had grown into a true guardian.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    helper = world.facts["helper"]
    tags = {"quest", "empower", "tree", "transformation"}
    if helper.id in {"lantern", "glow_moss"}:
        tags.add("lantern")
    if helper.id in {"cloak", "song_scarf"}:
        tags.add("cloak")
    if helper.id in {"rush_boat", "stepping_stones"}:
        tags.add("boat")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        source="moonwell",
        helper="lantern",
        name="Mira",
        gender="girl",
        elder="grandmother",
    ),
    StoryParams(
        source="sunpool",
        helper="cloak",
        name="Rowan",
        gender="boy",
        elder="grandfather",
    ),
    StoryParams(
        source="starlake",
        helper="rush_boat",
        name="Nessa",
        gender="girl",
        elder="grandmother",
    ),
    StoryParams(
        source="moonwell",
        helper="glow_moss",
        name="Ivo",
        gender="boy",
        elder="grandfather",
    ),
    StoryParams(
        source="starlake",
        helper="stepping_stones",
        name="Faye",
        gender="girl",
        elder="grandmother",
    ),
]


ASP_RULES = r"""
fits(S,H) :- source(S), helper(H), needs(S,N), solves(H,N).
valid(S,H) :- fits(S,H).

transformation(S,C) :- wing_color(S,C).
outcome(C) :- chosen_source(S), chosen_helper(H), fits(S,H), transformation(S,C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("needs", source_id, source.need))
        lines.append(asp.fact("wing_color", source_id, source.wing_color))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for need in sorted(helper.solves):
            lines.append(asp.fact("solves", helper_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP valid combos match Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        py_out = outcome_of(params)
        cl_out = asp_outcome(params)
        if py_out != cl_out:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcomes match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a young fairy goes on a quest, uses the right helper, heals a magical tree, and is transformed."
    )
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible source/helper pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.source not in SOURCES:
        raise StoryError(f"(Unknown source: {args.source})")
    if args.helper and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")
    if args.source and args.helper:
        source = SOURCES[args.source]
        helper = HELPERS[args.helper]
        if not helper_fits(source, helper):
            raise StoryError(explain_rejection(source, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.source is None or combo[0] == args.source)
        and (args.helper is None or combo[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    source_id, helper_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        source=source_id,
        helper=helper_id,
        name=name,
        gender=gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.elder not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown elder: {params.elder})")

    source = SOURCES[params.source]
    helper = HELPERS[params.helper]
    if not helper_fits(source, helper):
        raise StoryError(explain_rejection(source, helper))

    hero_type = "fairy_girl" if params.gender == "girl" else "fairy_boy"
    world = tell(
        source=source,
        helper=helper,
        hero_name=params.name,
        hero_type=hero_type,
        elder_type=params.elder,
        elder_name=params.elder.capitalize(),
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
        print(f"{len(combos)} compatible (source, helper) pairs:\n")
        for source_id, helper_id in combos:
            print(f"  {source_id:9} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
                f"### {sample.params.name}: {sample.params.source} with "
                f"{sample.params.helper} ({outcome_of(sample.params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
