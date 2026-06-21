#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/seventeenth_work_dim_flap_suspense_heartwarming.py
==============================================================================

A standalone story world about a child who hears a worrying sound behind a flap
in a dim apartment-service nook on the seventeenth floor. The story stays
heartwarming, but the middle carries suspense: something alive is trapped,
a careful grown-up is fetched, and the ending image proves the hallway has
changed from tense and echoing to warm and safe.

Run it
------
    python storyworlds/worlds/gpt-5.4/seventeenth_work_dim_flap_suspense_heartwarming.py
    python storyworlds/worlds/gpt-5.4/seventeenth_work_dim_flap_suspense_heartwarming.py --flap vent --creature parakeet
    python storyworlds/worlds/gpt-5.4/seventeenth_work_dim_flap_suspense_heartwarming.py --method broom_poke
    python storyworlds/worlds/gpt-5.4/seventeenth_work_dim_flap_suspense_heartwarming.py --all --qa
    python storyworlds/worlds/gpt-5.4/seventeenth_work_dim_flap_suspense_heartwarming.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.label or self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class FlapPlace:
    id: str = ""
    label: str = ""
    phrase: str = ""
    place_text: str = ""
    height: str = ""
    admits: set[str] = field(default_factory=set)
    sound: str = ""
    open_text: str = ""
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
class CreatureCfg:
    id: str = ""
    label: str = ""
    kind: str = ""
    sound: str = ""
    reveal: str = ""
    domestic: bool = False
    owner_name: str = ""
    owner_home: str = ""
    ending_text: str = ""
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
class RescueMethod:
    id: str = ""
    sense: int = 0
    helper_name: str = ""
    helper_type: str = ""
    helper_role: str = ""
    reaches: set[str] = field(default_factory=set)
    works_for: set[str] = field(default_factory=set)
    tool_text: str = ""
    approach_text: str = ""
    qa_text: str = ""
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
class StoryParams:
    flap: str = ""
    creature: str = ""
    method: str = ""
    child_name: str = ""
    child_gender: str = ""
    parent: str = ""
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


def _r_distress(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    hall = world.get("hall")
    child = world.get("child")
    flap = world.get("flap_obj")
    if creature.meters["trapped"] >= THRESHOLD:
        sig = ("distress", creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.memes["fear"] += 1
            hall.meters["tension"] += 1
            child.memes["worry"] += 1
            flap.meters["rattling"] += 1
            out.append("__suspense__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    child = world.get("child")
    hall = world.get("hall")
    if creature.meters["trapped"] < THRESHOLD and hall.meters["tension"] >= THRESHOLD:
        sig = ("relief", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["care"] += 1
            hall.meters["tension"] = 0.0
            out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="distress", tag="emotional", apply=_r_distress),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


def flap_allows(flap: FlapPlace, creature: CreatureCfg) -> bool:
    return creature.id in flap.admits


def sensible_methods() -> list[RescueMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_fits(method: RescueMethod, flap: FlapPlace, creature: CreatureCfg) -> bool:
    return flap.height in method.reaches and creature.id in method.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for flap_id, flap in FLAPS.items():
        for creature_id, creature in CREATURES.items():
            if not flap_allows(flap, creature):
                continue
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and method_fits(method, flap, creature):
                    combos.append((flap_id, creature_id, method_id))
    return sorted(combos)


def predict_need_help(world: World) -> dict:
    sim = world.copy()
    creature = sim.get("creature")
    creature.meters["trapped"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": creature.memes["fear"],
        "tension": sim.get("hall").meters["tension"],
    }


def introduce(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"After school, {child.id} rode the elevator up to the seventeenth floor with "
        f"{child.pronoun('possessive')} {parent.label_word}. In {child.pronoun('possessive')} hand "
        f"was the seventeenth paper heart for the hallway kindness string."
    )
    world.say(
        f"{child.id} loved that little job. Each new heart made the long corridor feel less lonely."
    )


def mystery_begins(world: World, child: Entity, flap: FlapPlace, creature: CreatureCfg) -> None:
    world.say(
        f"At the far end of the hall was {flap.place_text}, a work-dim corner where the bulbs were always sleepy."
    )
    world.say(
        f"Just as {child.id} reached up to tie the paper heart, {child.pronoun()} heard {flap.sound} from {flap.phrase}."
    )
    creature_ent = world.get("creature")
    creature_ent.meters["trapped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} stood very still. The sound came again, soft and worried, and the little flap trembled."
    )


def inspect(world: World, child: Entity, flap: FlapPlace, creature: CreatureCfg) -> None:
    pred = predict_need_help(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_tension"] = pred["tension"]
    child.memes["bravery"] += 1
    world.say(
        f"{child.pronoun().capitalize()} tiptoed closer and saw {creature.reveal} behind the flap."
    )
    world.say(
        f'"Something is stuck," {child.id} whispered. The sound was small, but it made the whole hall feel bigger and hushier.'
    )


def fetch_helper(world: World, child: Entity, parent: Entity, helper: Entity, method: RescueMethod) -> None:
    child.memes["care"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Instead of tugging at the flap alone, {child.id} hurried to find help."
    )
    if helper.role == "parent":
        world.say(
            f"{child.pronoun().capitalize()} told {parent.label_word} what {child.pronoun()} had heard, and {parent.label_word} came at once."
        )
    else:
        world.say(
            f"{child.pronoun().capitalize()} found {helper.id}, the {method.helper_role}, and told {helper.pronoun('object')} about the frightened sound."
        )
    world.say(
        f"{helper.id} nodded and brought {method.tool_text}."
    )


def rescue(world: World, child: Entity, helper: Entity, flap: FlapPlace, creature: CreatureCfg, method: RescueMethod) -> None:
    creature_ent = world.get("creature")
    flap_ent = world.get("flap_obj")
    flap_ent.meters["open"] += 1
    world.say(
        f"{helper.id} {method.approach_text} {flap.open_text}"
    )
    creature_ent.meters["trapped"] = 0.0
    creature_ent.memes["fear"] = 0.0
    creature_ent.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Out came {creature.label}, shaky for one moment and then still. {child.id} let out the breath {child.pronoun()} had been holding."
    )


def return_pet(world: World, child: Entity, creature: CreatureCfg) -> None:
    owner = creature.owner_name
    home = creature.owner_home
    world.say(
        f"Then a door opened at {home}, and {owner} gasped when they saw {creature.label}."
    )
    world.say(
        f'"There you are!" {owner} cried, gathering {creature.label} close. {child.id} smiled so hard {child.pronoun("possessive")} cheeks hurt.'
    )
    world.facts["outcome"] = "returned"


def release_bird(world: World, child: Entity, creature: CreatureCfg) -> None:
    world.say(
        f"{creature.ending_text} For a beat, {child.id} watched with both hands pressed to {child.pronoun('possessive')} heart."
    )
    world.say(
        f"Then the hall did not feel spooky at all anymore. It felt kind."
    )
    world.facts["outcome"] = "released"


def closing_image(world: World, child: Entity, flap: FlapPlace) -> None:
    world.say(
        f"When {child.id} finally tied up the paper heart, it hung near the once-rattling flap and barely moved."
    )
    world.say(
        "The seventeenth floor was quiet again, but now it was the quiet of safety, not suspense."
    )


def tell(
    flap: FlapPlace,
    creature_cfg: CreatureCfg,
    method: RescueMethod,
    child_name: str = "Nia",
    child_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(
        Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent")
    )
    helper_id = method.helper_name if method.helper_name != "Parent" else parent.label_word.capitalize()
    helper_type = method.helper_type if method.helper_name != "Parent" else parent_type
    helper_role = "parent" if method.helper_name == "Parent" else "helper"
    helper = world.add(
        Entity(
            id=helper_id,
            kind="character",
            type=helper_type,
            role=helper_role,
            label=method.helper_role,
        )
    )
    hall = world.add(Entity(id="hall", type="hallway", label="the hallway"))
    flap_ent = world.add(Entity(id="flap_obj", type="flap", label=flap.label, tags=set(flap.tags)))
    creature = world.add(
        Entity(
            id="creature",
            type=creature_cfg.kind,
            label=creature_cfg.label,
            role="creature",
            attrs={"domestic": creature_cfg.domestic},
            tags=set(creature_cfg.tags),
        )
    )

    child.memes["wonder"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["care"] = 0.0
    hall.meters["tension"] = 0.0
    flap_ent.meters["rattling"] = 0.0
    creature.meters["trapped"] = 0.0
    creature.meters["safe"] = 0.0
    creature.memes["fear"] = 0.0

    introduce(world, child, parent)
    world.para()
    mystery_begins(world, child, flap, creature_cfg)
    inspect(world, child, flap, creature_cfg)
    world.para()
    fetch_helper(world, child, parent, helper, method)
    rescue(world, child, helper, flap, creature_cfg, method)
    if creature_cfg.domestic:
        return_pet(world, child, creature_cfg)
    else:
        release_bird(world, child, creature_cfg)
    world.para()
    closing_image(world, child, flap)

    world.facts.update(
        child=child,
        parent=parent,
        helper=helper,
        flap=flap,
        creature_cfg=creature_cfg,
        method=method,
        trapped=creature.meters["safe"] < THRESHOLD,
        domestic=creature_cfg.domestic,
        outcome=world.facts.get("outcome", "returned" if creature_cfg.domestic else "released"),
    )
    return world


FLAPS = {
    "vent": FlapPlace(
        id="vent",
        label="vent flap",
        phrase="the metal vent flap outside the service closet",
        place_text="a narrow service nook with mops, paint cans, and folded caution signs",
        height="high",
        admits={"pigeon", "parakeet"},
        sound="a thin scrape, then a worried flap-flap",
        open_text="high above the floor.",
        tags={"vent_flap", "service_hall"},
    ),
    "window": FlapPlace(
        id="window",
        label="window flap",
        phrase="the old window flap beside the stairwell",
        place_text="the stairwell landing where the late sun reached only in a crooked stripe",
        height="middle",
        admits={"pigeon", "parakeet"},
        sound="a quick tap-tap and a restless flap",
        open_text="beside the stair rail.",
        tags={"window_flap", "service_hall"},
    ),
    "crawl": FlapPlace(
        id="crawl",
        label="crawlspace flap",
        phrase="the wooden crawlspace flap near the radiator pipes",
        place_text="a pipe corner under the mailboxes, warm and a little dusty",
        height="low",
        admits={"kitten", "puppy"},
        sound="a faint scratch-scratch and one scared flap of wood",
        open_text="down by the floor.",
        tags={"crawlspace", "service_hall"},
    ),
}

CREATURES = {
    "pigeon": CreatureCfg(
        id="pigeon",
        label="a gray pigeon",
        kind="bird",
        sound="coo",
        reveal="one bright eye and a blur of gray feathers",
        domestic=False,
        ending_text="Mr. Cruz set the pigeon on the open windowsill, and it gave one strong beat of its wings before sailing into the pink evening sky.",
        tags={"pigeon", "bird"},
    ),
    "parakeet": CreatureCfg(
        id="parakeet",
        label="a little green parakeet",
        kind="bird",
        sound="chirp",
        reveal="a tiny curved beak and green feathers tucked tight with fear",
        domestic=True,
        owner_name="Mrs. Rami from 17C",
        owner_home="17C",
        ending_text="",
        tags={"parakeet", "bird", "pet"},
    ),
    "kitten": CreatureCfg(
        id="kitten",
        label="a striped kitten",
        kind="cat",
        sound="mew",
        reveal="two round eyes and a little paw patting in the dark",
        domestic=True,
        owner_name="Owen from 17A",
        owner_home="17A",
        ending_text="",
        tags={"kitten", "pet"},
    ),
    "puppy": CreatureCfg(
        id="puppy",
        label="a small brown puppy",
        kind="dog",
        sound="whine",
        reveal="a wet nose and one floppy ear pressed into the crack",
        domestic=True,
        owner_name="Grandpa Luis from 17D",
        owner_home="17D",
        ending_text="",
        tags={"puppy", "pet"},
    ),
}

METHODS = {
    "ladder_towel": RescueMethod(
        id="ladder_towel",
        sense=3,
        helper_name="Mr. Cruz",
        helper_type="man",
        helper_role="superintendent",
        reaches={"high", "middle"},
        works_for={"pigeon", "parakeet"},
        tool_text="a short ladder and a soft towel",
        approach_text="set the ladder in place, climbed slowly, and spoke in a low steady voice as he lifted the flap",
        qa_text="used a short ladder and a soft towel to reach the trapped bird safely",
        tags={"ladder", "gentle_rescue"},
    ),
    "seed_crate": RescueMethod(
        id="seed_crate",
        sense=3,
        helper_name="Ms. Imani",
        helper_type="woman",
        helper_role="front-desk manager",
        reaches={"high", "middle"},
        works_for={"pigeon", "parakeet"},
        tool_text="a little pet crate and a scoop of seed",
        approach_text="opened the flap carefully and waited with patient hands while the tiny bird edged toward the seed",
        qa_text="coaxed the bird out with a little crate and seed",
        tags={"crate", "gentle_rescue"},
    ),
    "blanket_coax": RescueMethod(
        id="blanket_coax",
        sense=3,
        helper_name="Parent",
        helper_type="woman",
        helper_role="parent",
        reaches={"low", "middle"},
        works_for={"kitten", "puppy"},
        tool_text="a flashlight and a warm blanket",
        approach_text="knelt down, shone the light softly, and held the blanket ready while speaking in the calmest voice",
        qa_text="knelt with a flashlight and blanket and coaxed the little animal out gently",
        tags={"blanket", "call_adult", "gentle_rescue"},
    ),
    "broom_poke": RescueMethod(
        id="broom_poke",
        sense=1,
        helper_name="Mr. Dale",
        helper_type="man",
        helper_role="neighbor",
        reaches={"low", "middle", "high"},
        works_for={"pigeon", "parakeet", "kitten", "puppy"},
        tool_text="a broom",
        approach_text="jabbed the broom toward the opening and tried to scare the creature out of hiding",
        qa_text="poked at the opening with a broom",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Nia", "Mila", "Zoe", "Lena", "Ava", "Ruby", "Tara", "Maya"]
BOY_NAMES = ["Ben", "Eli", "Theo", "Noah", "Sam", "Omar", "Leo", "Finn"]


KNOWLEDGE = {
    "vent_flap": [
        (
            "What does a vent flap do?",
            "A vent flap is a small cover that opens and closes where air moves through a vent. It can rattle when wind pushes it.",
        )
    ],
    "window_flap": [
        (
            "Why might a loose window flap make noise?",
            "A loose window flap can tap and shake when wind or something behind it moves. Small sounds can seem extra mysterious in a quiet hall.",
        )
    ],
    "crawlspace": [
        (
            "What is a crawlspace flap?",
            "A crawlspace flap is a little door that covers a low storage or pipe space. It keeps the opening closed when nobody needs to go inside.",
        )
    ],
    "pigeon": [
        (
            "What is a pigeon?",
            "A pigeon is a city bird with strong wings and quick feet. If it gets trapped indoors, it can become scared and flap around.",
        )
    ],
    "parakeet": [
        (
            "What is a parakeet?",
            "A parakeet is a small pet bird with a curved beak and bright feathers. It needs gentle hands and a safe cage or home.",
        )
    ],
    "kitten": [
        (
            "Why should you be gentle with a kitten?",
            "Kittens are small and can frighten easily. A calm voice and soft hands help them feel safe.",
        )
    ],
    "puppy": [
        (
            "Why might a puppy hide when it is scared?",
            "A puppy may hide because dark little spaces can feel safer than a loud hallway. Once it feels calm again, it is more likely to come out.",
        )
    ],
    "ladder": [
        (
            "Why do grown-ups use a ladder for high places?",
            "A ladder helps a grown-up reach something high without climbing on unsafe furniture. It gives better balance and keeps both hands ready.",
        )
    ],
    "crate": [
        (
            "Why can a small crate help in an animal rescue?",
            "A crate gives a frightened animal a safe place to step into. That can feel calmer than being chased.",
        )
    ],
    "blanket": [
        (
            "How can a blanket help during a gentle rescue?",
            "A blanket can keep a small animal warm and help it feel tucked in and safe. It is softer and kinder than grabbing roughly.",
        )
    ],
    "call_adult": [
        (
            "What should a child do when an animal seems trapped?",
            "A child should tell a grown-up right away. Getting calm help fast is kinder and safer than struggling alone.",
        )
    ],
    "gentle_rescue": [
        (
            "Why is a gentle rescue better than a scary one?",
            "A gentle rescue keeps the animal from getting more frightened. Calm voices and careful tools make it easier to help without hurting it.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "vent_flap",
    "window_flap",
    "crawlspace",
    "pigeon",
    "parakeet",
    "kitten",
    "puppy",
    "ladder",
    "crate",
    "blanket",
    "call_adult",
    "gentle_rescue",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    flap = f["flap"]
    creature = f["creature_cfg"]
    outcome = f["outcome"]
    ending = "returns a pet to its owner" if outcome == "returned" else "sets a wild bird free"
    return [
        (
            'Write a heartwarming suspense story for a 3-to-5-year-old that includes the words '
            '"seventeenth", "work-dim", and "flap".'
        ),
        (
            f"Tell a gentle apartment-hall mystery where {child.id} hears a worried sound behind "
            f"{flap.phrase}, gets a careful grown-up, and {ending}."
        ),
        (
            f"Write a story with suspense in the middle and a warm ending, where a child notices "
            f"{creature.label} trapped near a flap on the seventeenth floor."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper = f["helper"]
    flap = f["flap"]
    creature = f["creature_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who heard a strange sound on the seventeenth floor, and the grown-up who helped. The story follows {child.pronoun('object')} from worry to relief.",
        ),
        (
            "What made the story feel suspenseful?",
            f"The little noise kept coming from {flap.phrase}, and {child.id} could not see the whole problem at first. That made the quiet hall feel tense until the flap was opened.",
        ),
        (
            f"Why did {child.id} get help instead of pulling on the flap alone?",
            f"{child.id} could tell something living was frightened behind the flap. Getting a grown-up was safer because the rescue needed calm hands and the right tools.",
        ),
        (
            f"How did the helper rescue the animal?",
            f"{helper.id} {method.qa_text}. That careful method kept the trapped creature from getting more scared.",
        ),
    ]
    if outcome == "returned":
        qa.append(
            (
                "What happened after the animal came out?",
                f"It turned out to be someone's pet, and {creature.owner_name} from {creature.owner_home} came to take it home. The ending feels warm because the frightened animal was safe again with its person.",
            )
        )
    else:
        qa.append(
            (
                "What happened after the bird came out?",
                f"The bird was set safely on an open windowsill and flew back into the evening sky. The scary sound stopped because the bird was no longer trapped.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the paper heart hanging near the flap while the hall felt peaceful again. The ending image shows that the same place that felt spooky now felt kind and safe.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["flap"].tags) | set(f["creature_cfg"].tags) | set(f["method"].tags)
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
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_flap_rejection(flap: FlapPlace, creature: CreatureCfg) -> str:
    allowed = ", ".join(sorted(flap.admits))
    return (
        f"(No story: {creature.label} does not fit the world model for {flap.label}. "
        f"That flap plausibly hides only: {allowed}.)"
    )


def explain_method_rejection(method: RescueMethod) -> str:
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method.id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try a gentler rescue like: {better}.)"
    )


def explain_combo_rejection(method: RescueMethod, flap: FlapPlace, creature: CreatureCfg) -> str:
    return (
        f"(No story: {method.id} is not a good rescue for {creature.id} at a {flap.height} flap. "
        f"The helper needs the right reach and the right gentle method for that animal.)"
    )


CURATED = [
    StoryParams(
        flap="vent",
        creature="parakeet",
        method="ladder_towel",
        child_name="Nia",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        flap="window",
        creature="pigeon",
        method="seed_crate",
        child_name="Eli",
        child_gender="boy",
        parent="father",
    ),
    StoryParams(
        flap="crawl",
        creature="kitten",
        method="blanket_coax",
        child_name="Ruby",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        flap="crawl",
        creature="puppy",
        method="blanket_coax",
        child_name="Theo",
        child_gender="boy",
        parent="father",
    ),
]


ASP_RULES = r"""
admissible(F, C) :- flap(F), creature(C), admits(F, C).
sensible(M) :- method(M), sense(M, S), sense_min(Mn), S >= Mn.
valid(F, C, M) :- admissible(F, C), sensible(M), height(F, H), reaches(M, H), works_for(M, C).

outcome(returned) :- chosen_creature(C), domestic(C).
outcome(released) :- chosen_creature(C), not domestic(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for flap_id, flap in FLAPS.items():
        lines.append(asp.fact("flap", flap_id))
        lines.append(asp.fact("height", flap_id, flap.height))
        for creature_id in sorted(flap.admits):
            lines.append(asp.fact("admits", flap_id, creature_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        if creature.domestic:
            lines.append(asp.fact("domestic", creature_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for height in sorted(method.reaches):
            lines.append(asp.fact("reaches", method_id, height))
        for creature_id in sorted(method.works_for):
            lines.append(asp.fact("works_for", method_id, creature_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_creature", params.creature)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    creature = CREATURES[params.creature]
    return "returned" if creature.domestic else "released"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combo gate matches ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = resolve_params(build_parser().parse_args([]), random.Random(7))
        sample = generate(smoke)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="")
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mysterious flap, a trapped creature, and a heartwarming rescue."
    )
    ap.add_argument("--flap", choices=FLAPS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.flap and args.creature:
        flap = FLAPS[args.flap]
        creature = CREATURES[args.creature]
        if not flap_allows(flap, creature):
            raise StoryError(explain_flap_rejection(flap, creature))
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            raise StoryError(explain_method_rejection(method))
        if args.flap and args.creature:
            flap = FLAPS[args.flap]
            creature = CREATURES[args.creature]
            if not method_fits(method, flap, creature):
                raise StoryError(explain_combo_rejection(method, flap, creature))

    combos = [
        combo
        for combo in valid_combos()
        if (args.flap is None or combo[0] == args.flap)
        and (args.creature is None or combo[1] == args.creature)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    flap_id, creature_id, method_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        flap=flap_id,
        creature=creature_id,
        method=method_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.flap not in FLAPS:
        raise StoryError(f"(Unknown flap: {params.flap})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    flap = FLAPS[params.flap]
    creature = CREATURES[params.creature]
    method = METHODS[params.method]

    if method.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(method))
    if not flap_allows(flap, creature):
        raise StoryError(explain_flap_rejection(flap, creature))
    if not method_fits(method, flap, creature):
        raise StoryError(explain_combo_rejection(method, flap, creature))

    world = tell(
        flap=flap,
        creature_cfg=creature,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (flap, creature, method) combos:\n")
        for flap, creature, method in combos:
            out = "returned" if CREATURES[creature].domestic else "released"
            print(f"  {flap:8} {creature:10} {method:13} -> {out}")
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
            header = f"### {p.child_name}: {p.creature} at {p.flap} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
