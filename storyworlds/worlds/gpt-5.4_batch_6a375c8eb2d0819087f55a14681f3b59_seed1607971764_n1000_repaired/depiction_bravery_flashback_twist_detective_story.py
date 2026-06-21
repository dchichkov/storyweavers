#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/depiction_bravery_flashback_twist_detective_story.py
==============================================================================

A standalone storyworld for a tiny child-facing detective story domain:
a young sleuth notices that an exhibit picture is missing, follows clues,
faces a dark place with bravery, remembers an earlier detail in a flashback,
and reaches a twist ending where the supposed thief was actually protecting it.

The domain is intentionally small and constraint-checked. A reasonable story
exists only when:

- the chosen setting really has the danger the helper is protecting the item from
- the chosen item is vulnerable to that danger
- the chosen hiding place can fit the item
- the chosen hiding place actually protects against that danger

The "detective" turn is state-driven:
- the item vanishes because the helper moved it
- the hero's flashback may point to the right place
- bravery determines whether the hero checks the dark hiding place before blaming

Run it
------
python storyworlds/worlds/gpt-5.4/depiction_bravery_flashback_twist_detective_story.py
python storyworlds/worlds/gpt-5.4/depiction_bravery_flashback_twist_detective_story.py --all
python storyworlds/worlds/gpt-5.4/depiction_bravery_flashback_twist_detective_story.py --qa
python storyworlds/worlds/gpt-5.4/depiction_bravery_flashback_twist_detective_story.py --trace
python storyworlds/worlds/gpt-5.4/depiction_bravery_flashback_twist_detective_story.py --json
python storyworlds/worlds/gpt-5.4/depiction_bravery_flashback_twist_detective_story.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    exhibit: str
    dangers: set[str]
    dark_place: str
    entry_sound: str
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
class MissingItem:
    id: str
    label: str
    phrase: str
    size: int
    vulnerable_to: set[str]
    reveal_image: str
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
class Hideout:
    id: str
    label: str
    phrase: str
    capacity: int
    protects_from: set[str]
    darkness: int
    clue: str
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
class Motive:
    id: str
    danger: str
    sign: str
    line: str
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
class Trait:
    id: str
    bravery: int
    style: str
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
class Memory:
    id: str
    clarity: int
    flashback: str
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


def _r_missing_mystery(world: World) -> list[str]:
    item = world.get("item")
    hero = world.get("hero")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["mystery"] += 1
    return []


def _r_hidden_safe(world: World) -> list[str]:
    item = world.get("item")
    hideout = world.get("hideout")
    if item.attrs.get("location") != hideout.id:
        return []
    sig = ("safe", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if hideout.attrs.get("protects_danger") and hideout.attrs.get("protects_danger") == world.facts.get("danger"):
        item.meters["protected"] += 1
    return []


def _r_blamed_hurt(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["blame"] < THRESHOLD:
        return []
    sig = ("hurt", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["hurt"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_mystery", tag="mystery", apply=_r_missing_mystery),
    Rule(name="hidden_safe", tag="physical", apply=_r_hidden_safe),
    Rule(name="blamed_hurt", tag="social", apply=_r_blamed_hurt),
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
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "library": Setting(
        id="library",
        place="the town library",
        exhibit="the reading corner's little art display",
        dangers={"drip"},
        dark_place="the old supply alcove behind the atlas shelf",
        entry_sound="the atlas shelf gave a soft wooden creak",
        tags={"library", "books"},
    ),
    "school": Setting(
        id="school",
        place="the school hallway",
        exhibit="the class mystery board",
        dangers={"draft"},
        dark_place="the prop closet beside the stage curtain",
        entry_sound="the closet door sighed on its hinges",
        tags={"school", "hallway"},
    ),
    "museum": Setting(
        id="museum",
        place="the children's museum corner",
        exhibit="the tiny detectives exhibit",
        dangers={"smudge"},
        dark_place="the storage nook under the puppet stairs",
        entry_sound="the little latch clicked in the quiet",
        tags={"museum", "exhibit"},
    ),
}

ITEMS = {
    "bird_poster": MissingItem(
        id="bird_poster",
        label="bird poster",
        phrase="a bright bird depiction poster",
        size=2,
        vulnerable_to={"drip", "draft"},
        reveal_image="the bird depiction gleamed straight and dry in its safe spot",
        tags={"poster", "depiction", "paper"},
    ),
    "castle_sketch": MissingItem(
        id="castle_sketch",
        label="castle sketch",
        phrase="a careful castle depiction sketch",
        size=1,
        vulnerable_to={"drip", "smudge"},
        reveal_image="the castle depiction rested flat, not a corner bent or blurred",
        tags={"sketch", "depiction", "paper"},
    ),
    "sea_map": MissingItem(
        id="sea_map",
        label="sea map",
        phrase="a long sea depiction map",
        size=3,
        vulnerable_to={"draft", "smudge"},
        reveal_image="the sea depiction map lay rolled and tidy, its blue lines safe",
        tags={"map", "depiction", "paper"},
    ),
}

HIDEOUTS = {
    "drawer": Hideout(
        id="drawer",
        label="drawer",
        phrase="a deep wooden drawer",
        capacity=1,
        protects_from={"drip", "smudge"},
        darkness=1,
        clue="a silver pushpin lay beside it",
        tags={"drawer"},
    ),
    "tube": Hideout(
        id="tube",
        label="storage tube",
        phrase="a tall storage tube",
        capacity=3,
        protects_from={"draft", "smudge"},
        darkness=1,
        clue="a paper band with a blue star was looped around it",
        tags={"tube"},
    ),
    "cabinet": Hideout(
        id="cabinet",
        label="cabinet",
        phrase="a tall cabinet",
        capacity=3,
        protects_from={"drip", "draft", "smudge"},
        darkness=3,
        clue="one brass handle still wobbled from being shut in a hurry",
        tags={"cabinet", "dark"},
    ),
}

MOTIVES = {
    "drip": Motive(
        id="drip",
        danger="drip",
        sign="a little wet circle on the table",
        line="a leak from a flower jar had started to drip nearby",
        tags={"water", "care"},
    ),
    "draft": Motive(
        id="draft",
        danger="draft",
        sign="the edge of a paper scrap fluttering",
        line="a draft from the open side door kept lifting loose papers",
        tags={"wind", "care"},
    ),
    "smudge": Motive(
        id="smudge",
        danger="smudge",
        sign="a gray thumbprint on a scrap sheet",
        line="sticky painty fingers from the craft table were wandering too close",
        tags={"paint", "care"},
    ),
}

TRAITS = {
    "bold": Trait(id="bold", bravery=3, style="bold", tags={"bravery"}),
    "steady": Trait(id="steady", bravery=2, style="steady", tags={"bravery"}),
    "nervous": Trait(id="nervous", bravery=1, style="nervous", tags={"bravery"}),
}

MEMORIES = {
    "clear": Memory(
        id="clear",
        clarity=2,
        flashback="Then a clear flashback popped into {hero}'s mind: {helper} had passed by carrying a cardboard tube and whispering, \"This will keep it safe.\"",
    ),
    "fuzzy": Memory(
        id="fuzzy",
        clarity=1,
        flashback="Then a fuzzy flashback brushed {hero}'s mind: {helper} had been hurrying somewhere with both hands full, looking worried rather than sneaky.",
    ),
    "none": Memory(
        id="none",
        clarity=0,
        flashback="",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Max", "Finn", "Theo"]
HELPER_NAMES = ["June", "Owen", "Ruby", "Cole", "Ivy", "Eli"]


def fits(item: MissingItem, hideout: Hideout) -> bool:
    return item.size <= hideout.capacity


def protects(setting: Setting, item: MissingItem, hideout: Hideout, motive: Motive) -> bool:
    return (
        motive.danger in setting.dangers
        and motive.danger in item.vulnerable_to
        and motive.danger in hideout.protects_from
    )


def valid_combo(setting_id: str, item_id: str, hideout_id: str, motive_id: str) -> bool:
    if setting_id not in SETTINGS or item_id not in ITEMS or hideout_id not in HIDEOUTS or motive_id not in MOTIVES:
        return False
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    hideout = HIDEOUTS[hideout_id]
    motive = MOTIVES[motive_id]
    return fits(item, hideout) and protects(setting, item, hideout, motive)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id in ITEMS:
            for hideout_id in HIDEOUTS:
                for motive_id in MOTIVES:
                    if valid_combo(setting_id, item_id, hideout_id, motive_id):
                        out.append((setting_id, item_id, hideout_id, motive_id))
    return sorted(out)


def outcome_of_params(params: "StoryParams") -> str:
    if params.hideout not in HIDEOUTS or params.trait not in TRAITS or params.memory not in MEMORIES:
        raise StoryError("(Invalid outcome inputs.)")
    courage = TRAITS[params.trait].bravery + MEMORIES[params.memory].clarity
    dark = HIDEOUTS[params.hideout].darkness
    if courage >= dark + 1:
        return "solved"
    if MEMORIES[params.memory].clarity >= 1:
        return "explained"
    return "blamed"


def predict_discovery(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hideout = sim.get("hideout")
    hero.memes["courage"] = hero.memes["bravery"] + hero.memes["memory"]
    will_enter = hero.memes["courage"] >= hideout.meters["darkness_need"] + 1
    return {"will_enter": will_enter, "darkness": hideout.meters["darkness_need"]}


def introduce(world: World, hero: Entity, adult: Entity, item: MissingItem) -> None:
    world.say(
        f"{hero.id} loved little mysteries, so {adult.label_word} let {hero.pronoun('object')} help set up "
        f"{world.setting.exhibit} in {world.setting.place}. On the middle stand sat {item.phrase}, "
        f"the picture everyone wanted to see first."
    )
    world.say(
        f"{hero.id} stood back like a tiny detective and admired the depiction for a moment, "
        f"trying to notice every line."
    )


def vanish(world: World, hero: Entity, helper: Entity, item_ent: Entity) -> None:
    item_ent.meters["missing"] += 1
    item_ent.attrs["location"] = "gone"
    propagate(world, narrate=False)
    hero.memes["alarm"] += 1
    world.say(
        f"But when {hero.id} turned around to fetch tape, the stand was empty. "
        f'"The picture is gone," {hero.pronoun()} whispered. {helper.id} looked up too, '
        f"and the whole room suddenly felt like a real case."
    )


def inspect_clue(world: World, hero: Entity, motive: Motive, hideout: Hideout) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} crouched down and searched for clues. There was {motive.sign}, and near "
        f"{world.setting.dark_place} there was {hideout.clue}."
    )


def flashback(world: World, hero: Entity, helper: Entity, memory: Memory) -> None:
    if memory.clarity <= 0:
        world.facts["flashback_happened"] = False
        return
    hero.memes["memory"] += memory.clarity
    world.facts["flashback_happened"] = True
    world.say(
        memory.flashback.format(hero=hero.id, helper=helper.id)
    )


def choose_path(world: World, hero: Entity, helper: Entity, hideout: Hideout, outcome: str) -> None:
    pred = predict_discovery(world)
    world.facts["predicted_darkness"] = pred["darkness"]
    if outcome == "solved":
        hero.memes["courage"] = hero.memes["bravery"] + hero.memes["memory"]
        world.say(
            f"{hero.id}'s stomach gave a small flip. {world.setting.entry_sound}, and {world.setting.dark_place} "
            f"looked dim and deep. Still, {hero.pronoun()} took a breath, held the clue tight in {hero.pronoun('possessive')} mind, "
            f"and stepped toward the dark place."
        )
    elif outcome == "explained":
        hero.memes["hesitation"] += 1
        world.say(
            f"{hero.id} remembered just enough to stop short of blaming anyone, but not enough to march into the dark place alone. "
            f'{hero.pronoun().capitalize()} turned to {helper.id} and asked, "Did you see where it went?"'
        )
    else:
        hero.memes["blame"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The clue felt thin and the dark place looked too spooky to search first. "
            f'"{helper.id}, did you take it?" {hero.id} blurted.'
        )


def reveal(world: World, hero: Entity, helper: Entity, adult: Entity, item_ent: Entity, item: MissingItem,
           hideout: Hideout, motive: Motive, outcome: str) -> None:
    item_ent.attrs["location"] = hideout.id
    item_ent.meters["missing"] = 0.0
    item_ent.meters["found"] += 1
    propagate(world, narrate=False)
    helper.memes["care"] += 1
    if outcome == "solved":
        world.say(
            f"Inside {hideout.phrase}, {hero.id} found the missing picture. {item.reveal_image}. "
            f"{helper.id} hurried over and blinked. \"You found it! I hid it because {motive.line},\" "
            f"{helper.pronoun()} said."
        )
    elif outcome == "explained":
        world.say(
            f'{helper.id} pointed toward {hideout.phrase}. "I moved it because {motive.line}," '
            f"{helper.pronoun()} explained. When they opened it, {item.reveal_image}."
        )
    else:
        world.say(
            f'{helper.id} looked hurt, then pointed with a shaky finger toward {hideout.phrase}. '
            f'"I moved it because {motive.line}. I was going to tell you," {helper.pronoun()} said. '
            f"When {adult.label_word} opened it, {item.reveal_image}."
        )
    world.say(
        "That was the twist of the case: the supposed thief had really been the picture's protector all along."
    )


def repair(world: World, hero: Entity, helper: Entity, adult: Entity, outcome: str) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["trust"] += 1
    if outcome == "blamed":
        world.say(
            f'{hero.id} felt heat rise in {hero.pronoun("possessive")} cheeks. '
            f'"I am sorry," {hero.pronoun()} said. "{helper.id}, you were helping, not hiding it for mean reasons."'
        )
    else:
        world.say(
            f'{adult.label_word.capitalize()} smiled at them both. "Good detectives look twice before they decide," '
            f"{adult.pronoun()} said."
        )


def ending(world: World, hero: Entity, helper: Entity, item: MissingItem) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Soon the picture was back where it belonged, and children gathered around it again. "
        f"{hero.id} stood beside {helper.id}, no longer hunting for a culprit but guarding the display together."
    )
    world.say(
        f"When the first little visitors pointed at the picture, {hero.id} grinned. "
        f"This time the case ended with a safer clue, a kinder heart, and {item.phrase} shining in plain sight."
    )


@dataclass
class StoryParams:
    setting: str
    item: str
    hideout: str
    motive: str
    trait: str
    memory: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
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


def tell(setting: Setting, item: MissingItem, hideout: Hideout, motive: Motive, trait: Trait, memory: Memory,
         hero_name: str = "Mia", hero_gender: str = "girl", helper_name: str = "Owen",
         helper_gender: str = "boy", adult_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait.id],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        label="the grown-up",
        role="adult",
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="picture",
        label=item.label,
        phrase=item.phrase,
        role="missing_item",
        tags=set(item.tags),
        attrs={"location": "display"},
    ))
    hideout_ent = world.add(Entity(
        id="hideout",
        kind="thing",
        type="hideout",
        label=hideout.label,
        phrase=hideout.phrase,
        role="hideout",
        tags=set(hideout.tags),
        attrs={"protects_danger": motive.danger},
    ))
    hideout_ent.meters["darkness_need"] = float(hideout.darkness)
    hero.memes["bravery"] = float(trait.bravery)
    hero.memes["memory"] = 0.0
    hero.memes["courage"] = 0.0
    world.facts["danger"] = motive.danger

    introduce(world, hero, adult, item)
    world.para()
    vanish(world, hero, helper, item_ent)
    inspect_clue(world, hero, motive, hideout)
    flashback(world, hero, helper, memory)

    world.para()
    outcome = outcome_of_params(StoryParams(
        setting=setting.id,
        item=item.id,
        hideout=hideout.id,
        motive=motive.id,
        trait=trait.id,
        memory=memory.id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        adult=adult_type,
        seed=None,
    ))
    choose_path(world, hero, helper, hideout, outcome)

    world.para()
    reveal(world, hero, helper, adult, item_ent, item, hideout, motive, outcome)
    repair(world, hero, helper, adult, outcome)

    world.para()
    ending(world, hero, helper, item)

    world.facts.update(
        hero=hero,
        helper=helper,
        adult=adult,
        item_cfg=item,
        hideout_cfg=hideout,
        motive=motive,
        trait=trait,
        memory_cfg=memory,
        outcome=outcome,
        found=item_ent.meters["found"] >= THRESHOLD,
        blamed=hero.memes["blame"] >= THRESHOLD,
        flashback_happened=world.facts.get("flashback_happened", False),
        item=item_ent,
        hideout=hideout_ent,
    )
    return world


KNOWLEDGE = {
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to explain what happened. A good detective does not guess too fast, because clues can change the whole story.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick memory of something that happened earlier. It can help a character understand a clue in the present.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel scared. It does not mean never feeling fear at all.",
        )
    ],
    "twist": [
        (
            "What is a twist ending?",
            "A twist ending is when the truth turns out to be different from what people first believed. It makes earlier clues mean something new.",
        )
    ],
    "paper": [
        (
            "Why do paper pictures need protection?",
            "Paper can tear, blur, or get ruined by water, wind, or messy hands. That is why careful people keep important pictures in safe places.",
        )
    ],
    "water": [
        (
            "Why is dripping water bad for a paper picture?",
            "Water can make paper wrinkle and smear the colors or lines. Even a small drip can spoil a careful picture.",
        )
    ],
    "wind": [
        (
            "Why can a draft be a problem for loose paper?",
            "Moving air can lift a paper and bend or blow it away. A strong draft can ruin a neat display very quickly.",
        )
    ],
    "paint": [
        (
            "Why are sticky painty fingers risky near a picture?",
            "Paint or sticky smudges can mark the paper and hide the drawing underneath. Once a picture is smeared, it may be hard to clean.",
        )
    ],
}

KNOWLEDGE_ORDER = ["detective", "flashback", "bravery", "twist", "paper", "water", "wind", "paint"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item_cfg"]
    setting = world.setting
    motive = f["motive"]
    out = f["outcome"]
    base = (
        f'Write a child-friendly detective story set in {setting.place} where a young sleuth notices that {item.phrase} is missing.'
    )
    if out == "solved":
        return [
            base,
            f"Tell a detective story where {hero.id} uses bravery and a flashback to follow clues into a dark place and solve the case before blaming {helper.id}.",
            'Write a mystery with the word "depiction" and a twist ending where the supposed thief was really protecting the missing picture.',
        ]
    if out == "explained":
        return [
            base,
            f"Tell a gentle detective story where a flashback keeps {hero.id} from making a mean guess, and the truth is explained before the mystery grows worse.",
            f'Write a story with "depiction," bravery, flashback, and a twist, where the missing picture was moved because {motive.line}.',
        ]
    return [
        base,
        f"Tell a detective story where {hero.id} feels too scared to search the dark place first, blurts out a wrong accusation, and then learns the twist.",
        'Write a mystery using the word "depiction" where the first guess is wrong and the ending teaches the detective to look twice before deciding.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    adult = f["adult"]
    item = f["item_cfg"]
    hideout = f["hideout_cfg"]
    motive = f["motive"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who loves mysteries, and {helper.id}, who was helping at the display. The grown-up was there too, but the case mostly turned on what the two children understood about the missing picture.",
        ),
        (
            "What went missing?",
            f"The missing item was {item.phrase}. It mattered because it was the picture everyone wanted to see at the display.",
        ),
        (
            "Why was the picture moved?",
            f"It was moved because {motive.line}. The helper was trying to protect the picture from danger, not steal it.",
        ),
    ]
    if f.get("flashback_happened"):
        qa.append(
            (
                f"How did the flashback help {hero.id}?",
                f"The flashback reminded {hero.id} that {helper.id} had looked worried, not sneaky. That memory pushed the mystery toward the truth instead of toward a wrong guess.",
            )
        )
    if outcome == "solved":
        qa.append(
            (
                f"How did bravery matter in the story?",
                f"{hero.id} felt scared of {world.setting.dark_place}, but went in anyway to check the clue. That brave choice let {hero.pronoun()} find the picture before blaming anyone.",
            )
        )
        qa.append(
            (
                "What was the twist?",
                f"The twist was that the supposed thief was actually the protector. {helper.id} had hidden the picture in {hideout.phrase} so it would stay safe.",
            )
        )
    elif outcome == "explained":
        qa.append(
            (
                f"Did {hero.id} accuse {helper.id} right away?",
                f"No. {hero.id} hesitated and asked a question first because the memory was strong enough to slow {hero.pronoun('object')} down. That pause gave the truth room to come out kindly.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the picture safely returned to the display and the two children guarding it together. The ending shows that the mystery became teamwork instead of a quarrel.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} accuse {helper.id}?",
                f"{hero.id} felt unsure and the dark hiding place seemed too scary to search first. Without a strong enough memory to guide {hero.pronoun('object')}, {hero.pronoun()} guessed too fast.",
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn after the twist?",
                f"{hero.id} learned that clues should be checked before blaming a friend. The apology mattered because {helper.id} had been caring for the picture all along.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "bravery", "twist", "paper"}
    if world.facts.get("flashback_happened"):
        tags.add("flashback")
    motive = world.facts["motive"]
    tags |= set(motive.tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="library",
        item="bird_poster",
        hideout="cabinet",
        motive="drip",
        trait="bold",
        memory="clear",
        hero="Mia",
        hero_gender="girl",
        helper="Owen",
        helper_gender="boy",
        adult="mother",
        seed=None,
    ),
    StoryParams(
        setting="museum",
        item="castle_sketch",
        hideout="drawer",
        motive="smudge",
        trait="steady",
        memory="fuzzy",
        hero="Ben",
        hero_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        adult="father",
        seed=None,
    ),
    StoryParams(
        setting="school",
        item="sea_map",
        hideout="cabinet",
        motive="draft",
        trait="nervous",
        memory="none",
        hero="Leo",
        hero_gender="boy",
        helper="June",
        helper_gender="girl",
        adult="mother",
        seed=None,
    ),
    StoryParams(
        setting="library",
        item="castle_sketch",
        hideout="drawer",
        motive="drip",
        trait="steady",
        memory="clear",
        hero="Nora",
        hero_gender="girl",
        helper="Eli",
        helper_gender="boy",
        adult="father",
        seed=None,
    ),
]


def explain_rejection(setting_id: str, item_id: str, hideout_id: str, motive_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if hideout_id not in HIDEOUTS:
        return f"(No story: unknown hideout '{hideout_id}'.)"
    if motive_id not in MOTIVES:
        return f"(No story: unknown motive '{motive_id}'.)"
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    hideout = HIDEOUTS[hideout_id]
    motive = MOTIVES[motive_id]
    if motive.danger not in setting.dangers:
        return (
            f"(No story: {setting.place} does not have the {motive.danger} problem, so there is no reason to hide the picture for that cause.)"
        )
    if motive.danger not in item.vulnerable_to:
        return (
            f"(No story: {item.phrase} would not be harmed by {motive.danger}, so the detective twist would not make sense.)"
        )
    if not fits(item, hideout):
        return (
            f"(No story: {item.phrase} is too large for {hideout.phrase}, so the missing-picture clue would be unreasonable.)"
        )
    if motive.danger not in hideout.protects_from:
        return (
            f"(No story: {hideout.phrase} would not protect the picture from {motive.danger}, so the helper's plan would not be sensible.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
fits(I,H) :- item_size(I,S), hideout_capacity(H,C), S <= C.
need_protection(S,I,M) :- setting(S), item(I), motive(M), setting_has(S,D), vulnerable(I,D), motive_danger(M,D).
safe_hideout(H,M) :- hideout(H), motive(M), hideout_blocks(H,D), motive_danger(M,D).
valid(S,I,H,M) :- setting(S), item(I), hideout(H), motive(M),
                  fits(I,H), need_protection(S,I,M), safe_hideout(H,M).

courage(T,Mem,V) :- bravery(T,B), memory(Mem,C), V = B + C.
solved(H,T,Mem) :- hideout_dark(H,D), courage(T,Mem,V), V >= D + 1.
explained(H,T,Mem) :- hideout_dark(H,D), courage(T,Mem,V), V < D + 1, memory(Mem,C), C >= 1.
blamed(H,T,Mem) :- hideout_dark(H,D), courage(T,Mem,V), V < D + 1, memory(Mem,0).

outcome(H,T,Mem,solved) :- solved(H,T,Mem).
outcome(H,T,Mem,explained) :- explained(H,T,Mem).
outcome(H,T,Mem,blamed) :- blamed(H,T,Mem).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for danger in sorted(setting.dangers):
            lines.append(asp.fact("setting_has", setting_id, danger))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_size", item_id, item.size))
        for danger in sorted(item.vulnerable_to):
            lines.append(asp.fact("vulnerable", item_id, danger))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        lines.append(asp.fact("hideout_capacity", hideout_id, hideout.capacity))
        lines.append(asp.fact("hideout_dark", hideout_id, hideout.darkness))
        for danger in sorted(hideout.protects_from):
            lines.append(asp.fact("hideout_blocks", hideout_id, danger))
    for motive_id, motive in MOTIVES.items():
        lines.append(asp.fact("motive", motive_id))
        lines.append(asp.fact("motive_danger", motive_id, motive.danger))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("bravery", trait_id, trait.bravery))
    for memory_id, memory in MEMORIES.items():
        lines.append(asp.fact("memory", memory_id))
        lines.append(asp.fact("memory", memory_id, memory.clarity))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_memory", params.memory),
            "outcome_pick(O) :- chosen_hideout(H), chosen_trait(T), chosen_memory(M), outcome(H,T,M,O).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome_pick/1."))
    atoms = asp.atoms(model, "outcome_pick")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    rng = random.Random(99)
    parser = build_parser()
    for i in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(rng.randint(0, 10_000)))
            params.seed = i
            cases.append(params)
        except StoryError:
            rc = 1
            print("resolve_params unexpectedly failed during verify.")
            break
    mismatches = 0
    for params in cases:
        py_out = outcome_of_params(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome results differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        buf = io.StringIO()
        prev = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = prev
        if "depiction" not in sample.story:
            raise StoryError("Smoke test story did not include required word 'depiction'.")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny detective-story world: a missing picture, a brave search, a flashback clue, and a twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def pick_helper_name(rng: random.Random, avoid: str = "") -> str:
    choices = [name for name in HELPER_NAMES if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.hideout and args.motive:
        if not valid_combo(args.setting, args.item, args.hideout, args.motive):
            raise StoryError(explain_rejection(args.setting, args.item, args.hideout, args.motive))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.motive is None or combo[3] == args.motive)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, hideout_id, motive_id = rng.choice(combos)
    trait_id = args.trait or rng.choice(sorted(TRAITS))
    memory_id = args.memory or rng.choice(sorted(MEMORIES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or pick_name(rng, hero_gender)
    helper_name = args.helper or pick_helper_name(rng, avoid=hero_name)
    adult = args.adult or rng.choice(["mother", "father"])

    return StoryParams(
        setting=setting_id,
        item=item_id,
        hideout=hideout_id,
        motive=motive_id,
        trait=trait_id,
        memory=memory_id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        adult=adult,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(No story: unknown hideout '{params.hideout}'.)")
    if params.motive not in MOTIVES:
        raise StoryError(f"(No story: unknown motive '{params.motive}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(No story: unknown trait '{params.trait}'.)")
    if params.memory not in MEMORIES:
        raise StoryError(f"(No story: unknown memory '{params.memory}'.)")
    if not valid_combo(params.setting, params.item, params.hideout, params.motive):
        raise StoryError(explain_rejection(params.setting, params.item, params.hideout, params.motive))

    world = tell(
        setting=SETTINGS[params.setting],
        item=ITEMS[params.item],
        hideout=HIDEOUTS[params.hideout],
        motive=MOTIVES[params.motive],
        trait=TRAITS[params.trait],
        memory=MEMORIES[params.memory],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
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
        print(asp_program("", "#show valid/4.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, item, hideout, motive) combos:\n")
        for setting_id, item_id, hideout_id, motive_id in combos:
            print(f"  {setting_id:8} {item_id:13} {hideout_id:8} {motive_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.setting} / {p.item} / {p.hideout} / {outcome_of_params(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
