#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hygienist_viking_fetch_happy_ending_fable.py
========================================================================

A small storyworld about a child dressed as a viking, a kindly hygienist, and a
faithful animal helper asked to fetch the right cleaning tool. The little tale
is modeled as a fable-shaped simulation: sticky sweets lead to a sore mouth,
wise help leads to gentle care, and the ending proves that real bravery can be
clean and calm.

Run it
------
    python storyworlds/worlds/gpt-5.4/hygienist_viking_fetch_happy_ending_fable.py
    python storyworlds/worlds/gpt-5.4/hygienist_viking_fetch_happy_ending_fable.py --treat berry_taffy --helper pony --tool full_kit
    python storyworlds/worlds/gpt-5.4/hygienist_viking_fetch_happy_ending_fable.py --helper raven --tool full_kit
    python storyworlds/worlds/gpt-5.4/hygienist_viking_fetch_happy_ending_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hygienist_viking_fetch_happy_ending_fable.py --all
    python storyworlds/worlds/gpt-5.4/hygienist_viking_fetch_happy_ending_fable.py --verify
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
LISTENING_TRAITS = {"thoughtful", "gentle", "careful"}
BELOVED_HELPERS = {"puppy", "pony"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    can_fetch: bool = False
    fetch_capacity: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hygienist"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Treat:
    id: str
    label: str
    phrase: str
    crumbs: str
    stickiness: int
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
class Fetcher:
    id: str
    label: str
    type: str
    phrase: str
    capacity: int
    step: str
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
class Tool:
    id: str
    label: str
    phrase: str
    power: int
    weight: int
    method: str
    qa_text: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_sticky_aches(world: World) -> list[str]:
    mouth = world.get("mouth")
    hero = world.get("hero")
    if mouth.meters["sticky"] < THRESHOLD or mouth.meters["clean"] >= THRESHOLD:
        return []
    sig = ("ache", int(mouth.meters["sticky"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["ache"] += 1
    hero.memes["worry"] += 1
    return ["__ache__"]


def _r_clean_relief(world: World) -> list[str]:
    mouth = world.get("mouth")
    hero = world.get("hero")
    if mouth.meters["clean"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mouth.meters["sticky"] = 0.0
    hero.meters["ache"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["confidence"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="sticky_aches", tag="physical", apply=_r_sticky_aches),
    Rule(name="clean_relief", tag="physical", apply=_r_clean_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


def tool_can_help(treat: Treat, tool: Tool) -> bool:
    return tool.power >= treat.stickiness


def helper_can_fetch(fetcher: Fetcher, tool: Tool) -> bool:
    return fetcher.capacity >= tool.weight


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for treat_id, treat in TREATS.items():
        for helper_id, helper in HELPERS.items():
            for tool_id, tool in TOOLS.items():
                if tool_can_help(treat, tool) and helper_can_fetch(helper, tool):
                    out.append((treat_id, helper_id, tool_id))
    return out


def explain_rejection(treat: Treat, helper: Fetcher, tool: Tool) -> str:
    if not tool_can_help(treat, tool):
        return (
            f"(No story: {tool.phrase} is too weak to clean {treat.phrase}. "
            f"Pick a stronger tool for something that sticky.)"
        )
    if not helper_can_fetch(helper, tool):
        return (
            f"(No story: {helper.label} cannot fetch {tool.phrase}. "
            f"Choose a lighter tool or a stronger helper.)"
        )
    return "(No story: this combination does not fit the world.)"


def would_accept_quickly(trait: str, helper_id: str) -> bool:
    return trait in LISTENING_TRAITS or helper_id in BELOVED_HELPERS


def outcome_of(params: "StoryParams") -> str:
    return "quick" if would_accept_quickly(params.trait, params.helper) else "pause"


def predict_untended_ache(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    return {
        "ache": hero.meters["ache"],
        "worry": hero.memes["worry"],
    }


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"In a windy harbor town, {hero.id} tied on a paper helmet with small silver horns "
        f"and declared {hero.pronoun('object')}self a little viking for the day."
    )
    world.say(
        f"At {hero.pronoun('possessive')} heels trotted {helper.label}, who loved to fetch "
        f"whatever could be carried and always listened for a call."
    )


def feast_setup(world: World, hero: Entity, treat: Treat) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"Before the harbor cheer began, {hero.id} was given {treat.phrase}. "
        f"{hero.pronoun().capitalize()} ate it with such delight that {treat.crumbs} clung "
        f"to teeth and tongue."
    )


def try_to_cheer(world: World, hero: Entity) -> None:
    world.say(
        f"When the children lined up to roar like brave vikings and grin at the crowd, "
        f"{hero.id} opened {hero.pronoun('possessive')} mouth wide."
    )


def ache_turn(world: World, hero: Entity) -> None:
    if hero.meters["ache"] >= THRESHOLD:
        world.say(
            f"But the sticky sweetness tugged at one sore place, and {hero.id}'s roar came out "
            f"small. {hero.pronoun().capitalize()} pressed a hand to {hero.pronoun('possessive')} cheek."
        )


def hygienist_warn(world: World, hygienist: Entity, hero: Entity, tool: Tool) -> None:
    pred = predict_untended_ache(world)
    world.facts["predicted_ache"] = pred["ache"]
    world.say(
        f"Nearby stood Mira the hygienist, who kept a booth with cups, brushes, and kind advice. "
        f"She knelt beside {hero.id} and said, "
        f"\"A brave mouth needs care as much as a brave heart. If that sugar stays there, your smile "
        f"will hurt more before the cheer is done. Let someone fetch {tool.phrase}, and I will help.\""
    )


def proud_pause(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} puffed up at first. \"A viking should not fuss over one sticky little bite,\" "
        f"{hero.pronoun()} said, though the words were not as bold as {hero.pronoun()} hoped."
    )


def softening(world: World, hero: Entity) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"Then another ache pinched, and pride seemed smaller than comfort. {hero.id} took a slow breath "
        f"and looked back at the kindly hygienist."
    )


def ask_fetch(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"\"Please fetch {tool.phrase},\" {hero.id} said. At once {helper.label} {helper.attrs['step']} away, "
        f"found it, and came back with a proud little {helper.attrs['sound']}."
    )
    world.facts["fetched"] = True


def clean_mouth(world: World, hygienist: Entity, hero: Entity, tool: Tool) -> None:
    mouth = world.get("mouth")
    mouth.meters["clean"] += 1
    propagate(world, narrate=False)
    hero.memes["gratitude"] += 1
    world.say(
        f"Mira used {tool.phrase} and {tool.method}. Soon the sticky place was gone, and the sore feeling "
        f"melted away."
    )


def ending(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"When the cheer began again, {hero.id} lifted {hero.pronoun('possessive')} chin, gave a bright viking roar, "
        f"and smiled so wide that the harbor gulls seemed to answer."
    )
    world.say(
        f"{helper.label.capitalize()} danced in a happy circle, proud of the fetch, and Mira the hygienist "
        f"laughed to see such a clean, fearless grin."
    )
    world.say(
        f"From that day on, {hero.id} remembered that the strongest kind of courage is the kind that listens "
        f"before trouble grows."
    )


def tell(
    *,
    treat: Treat,
    fetcher: Fetcher,
    tool: Tool,
    hero_name: str,
    hero_gender: str,
    trait: str,
    parent_type: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            traits=[trait, "brave"],
            role="hero",
            attrs={"display_name": hero_name},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=fetcher.type,
            label=fetcher.label,
            role="helper",
            can_fetch=True,
            fetch_capacity=fetcher.capacity,
            attrs={"step": fetcher.step, "sound": fetcher.sound},
        )
    )
    hygienist = world.add(
        Entity(
            id="hygienist",
            kind="character",
            type="hygienist",
            label="Mira",
            role="hygienist",
        )
    )
    world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    mouth = world.add(
        Entity(
            id="mouth",
            kind="thing",
            type="mouth",
            label="mouth",
            role="mouth",
        )
    )
    mouth.meters["sticky"] = 0.0
    mouth.meters["clean"] = 0.0
    hero.meters["ache"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 0.0
    hero.memes["pride"] = 0.0
    helper.memes["joy"] = 0.0
    world.facts["fetched"] = False

    introduce(world, hero, helper)
    feast_setup(world, hero, treat)
    mouth.meters["sticky"] += float(treat.stickiness)

    world.para()
    try_to_cheer(world, hero)
    propagate(world, narrate=False)
    ache_turn(world, hero)
    hygienist_warn(world, hygienist, hero, tool)

    world.para()
    if would_accept_quickly(trait, fetcher.id):
        world.facts["outcome"] = "quick"
    else:
        world.facts["outcome"] = "pause"
        proud_pause(world, hero)
        softening(world, hero)
    ask_fetch(world, hero, helper, tool)

    world.para()
    clean_mouth(world, hygienist, hero, tool)
    ending(world, hero, helper)

    world.facts.update(
        hero=hero,
        helper=helper,
        hygienist=hygienist,
        treat=treat,
        tool=tool,
        mouth=mouth,
        trait=trait,
        ache_happened=hero.memes["worry"] >= THRESHOLD,
        cleaned=mouth.meters["clean"] >= THRESHOLD,
        happy=True,
    )
    return world


TREATS = {
    "honey_cake": Treat(
        id="honey_cake",
        label="honey cake",
        phrase="a warm honey cake",
        crumbs="golden honey crumbs",
        stickiness=2,
        tags={"sweet", "teeth", "honey"},
    ),
    "berry_taffy": Treat(
        id="berry_taffy",
        label="berry taffy",
        phrase="a twist of berry taffy",
        crumbs="purple sticky threads",
        stickiness=3,
        tags={"sweet", "teeth", "taffy"},
    ),
    "jam_roll": Treat(
        id="jam_roll",
        label="jam roll",
        phrase="a soft jam roll",
        crumbs="bright jam smears",
        stickiness=1,
        tags={"sweet", "teeth", "jam"},
    ),
}

HELPERS = {
    "puppy": Fetcher(
        id="puppy",
        label="the puppy",
        type="animal",
        phrase="a loyal puppy",
        capacity=1,
        step="bounded",
        sound="yip",
        tags={"fetch", "dog"},
    ),
    "raven": Fetcher(
        id="raven",
        label="the raven",
        type="animal",
        phrase="a clever raven",
        capacity=1,
        step="flapped",
        sound="caw",
        tags={"fetch", "bird"},
    ),
    "goat": Fetcher(
        id="goat",
        label="the goat",
        type="animal",
        phrase="a sure-footed goat",
        capacity=2,
        step="clattered",
        sound="maa",
        tags={"fetch", "goat"},
    ),
    "pony": Fetcher(
        id="pony",
        label="the pony",
        type="animal",
        phrase="a patient pony",
        capacity=3,
        step="trotted",
        sound="snort",
        tags={"fetch", "pony"},
    ),
}

TOOLS = {
    "floss_pick": Tool(
        id="floss_pick",
        label="floss pick",
        phrase="the little floss pick",
        power=1,
        weight=1,
        method="gently lifting the trapped sweetness from between the teeth",
        qa_text="used the little floss pick to lift the sticky bit away",
        tags={"hygienist", "floss"},
    ),
    "travel_brush": Tool(
        id="travel_brush",
        label="travel brush",
        phrase="the travel brush",
        power=2,
        weight=1,
        method="making small careful circles until the sugar loosened",
        qa_text="used the travel brush in careful circles",
        tags={"hygienist", "brush"},
    ),
    "full_kit": Tool(
        id="full_kit",
        label="full cleaning kit",
        phrase="the full cleaning kit",
        power=3,
        weight=3,
        method="working with brush, floss, and rinse until every sticky patch was clean",
        qa_text="used the full cleaning kit until every sticky patch was clean",
        tags={"hygienist", "brush", "floss"},
    ),
}

GIRL_NAMES = ["Liv", "Inga", "Freya", "Mira", "Sigrid", "Tova", "Edda"]
BOY_NAMES = ["Leif", "Oskar", "Rune", "Bo", "Ivar", "Nils", "Arne"]
TRAITS = ["thoughtful", "gentle", "careful", "stubborn", "proud", "hasty"]


@dataclass
class StoryParams:
    treat: str
    helper: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
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
    "hygienist": [
        (
            "What does a hygienist do?",
            "A hygienist helps keep teeth and gums clean and healthy. They use gentle tools and teach people how to care for their mouths."
        )
    ],
    "teeth": [
        (
            "Why can sticky sweets make your mouth hurt?",
            "Sticky sweets can cling to teeth and hide in small places. If they stay there, they can make a sore spot feel worse."
        )
    ],
    "brush": [
        (
            "What does a toothbrush do?",
            "A toothbrush sweeps food and sugar off teeth. Small gentle circles help clean the hard-to-reach places."
        )
    ],
    "floss": [
        (
            "What is floss for?",
            "Floss cleans between teeth where a brush may not fit. It helps lift out little bits of food."
        )
    ],
    "fetch": [
        (
            "What does fetch mean?",
            "To fetch means to go get something and bring it back. Dogs do it in games, and people can ask for a fetch when they need help."
        )
    ],
    "dog": [
        (
            "Why are dogs good at fetch?",
            "Many dogs like running after a thing and bringing it back. They enjoy the game and like helping their people."
        )
    ],
    "bird": [
        (
            "Why might a raven be a good helper in a story?",
            "Ravens are often shown as clever birds in tales. A clever helper can notice where something is and bring it back quickly."
        )
    ],
    "goat": [
        (
            "What makes a goat good on rocky ground?",
            "Goats are steady on their feet and good at balancing. That helps them carry things over uneven ground."
        )
    ],
    "pony": [
        (
            "Why can a pony carry more than a puppy?",
            "A pony is bigger and stronger than a puppy. Its larger body can carry heavier things."
        )
    ],
    "honey": [
        (
            "Why is honey sticky?",
            "Honey is thick and sugary, so it clings to fingers and teeth. That is why it needs wiping or brushing away."
        )
    ],
    "taffy": [
        (
            "Why is taffy so chewy?",
            "Taffy is stretched sugar, so it bends and pulls instead of crumbling. That makes it tasty, but also very sticky."
        )
    ],
    "jam": [
        (
            "What is jam made from?",
            "Jam is made from fruit and sugar cooked together. It is soft and sweet and can leave a smear if it drips."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "hygienist",
    "teeth",
    "brush",
    "floss",
    "fetch",
    "dog",
    "bird",
    "goat",
    "pony",
    "honey",
    "taffy",
    "jam",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treat = f["treat"]
    helper = f["helper"]
    tool = f["tool"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "hygienist", "viking", and "fetch", and ends happily.',
        f"Tell a gentle story where {hero.attrs['display_name']} dresses like a little viking, gets sticky teeth from {treat.label}, and asks {helper.label} to fetch {tool.phrase}.",
        f"Write a child-facing moral tale about bravery, listening, and mouth care, with a kindly hygienist and a cheerful ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    treat = f["treat"]
    tool = f["tool"]
    hygienist = f["hygienist"]
    hero_name = hero.attrs["display_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child pretending to be a little viking, {helper.label} who could fetch, and {hygienist.label} the hygienist. They all helped turn a sore moment into a happy one."
        ),
        (
            f"Why did {hero_name}'s mouth start to hurt?",
            f"{hero_name} ate {treat.phrase}, and its sticky sweetness clung to teeth and tongue. When the cheering began, that sticky spot tugged at a sore place and made roaring hard."
        ),
        (
            f"What did the hygienist tell {hero_name}?",
            f"{hygienist.label} said that a brave mouth needs care as much as a brave heart. She warned that if the sugar stayed there, the smile would hurt more before the cheer was done."
        ),
        (
            f"What did {helper.label} fetch?",
            f"{helper.label.capitalize()} fetched {tool.phrase}. That let the hygienist clean the sticky place instead of leaving the sore bit to grow worse."
        ),
        (
            f"How was the problem solved?",
            f"{hygienist.label} {tool.qa_text}. After that, the sticky place was gone and the ache melted away."
        ),
    ]
    if f["outcome"] == "pause":
        qa.append(
            (
                f"Did {hero_name} listen right away?",
                f"No. {hero_name} tried to act proud first and said a viking should not fuss. Then another ache pinched, and that helped {hero.pronoun('object')} understand that accepting care was the wiser brave choice."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero_name} listen right away?",
                f"Yes. {hero_name} trusted the advice quickly and asked for help at once. Listening early kept the sore mouth from bothering the cheer any longer."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily: {hero_name} gave a bright viking roar and a wide clean smile. The ending shows that good care changed pain into confidence."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"hygienist", "teeth", "fetch"}
    tags |= set(world.facts["tool"].tags)
    tags |= set(world.facts["helper"].attrs.get("tags", []))
    tags |= set(world.facts["treat"].tags)
    helper_id = world.facts["helper"].id
    if helper_id == "puppy":
        tags.add("dog")
    elif helper_id == "raven":
        tags.add("bird")
    elif helper_id == "goat":
        tags.add("goat")
    elif helper_id == "pony":
        tags.add("pony")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.can_fetch:
            bits.append(f"fetch_capacity={ent.fetch_capacity}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        treat="honey_cake",
        helper="puppy",
        tool="travel_brush",
        name="Liv",
        gender="girl",
        parent="mother",
        trait="gentle",
        seed=1,
    ),
    StoryParams(
        treat="berry_taffy",
        helper="pony",
        tool="full_kit",
        name="Leif",
        gender="boy",
        parent="father",
        trait="proud",
        seed=2,
    ),
    StoryParams(
        treat="jam_roll",
        helper="raven",
        tool="floss_pick",
        name="Edda",
        gender="girl",
        parent="mother",
        trait="thoughtful",
        seed=3,
    ),
    StoryParams(
        treat="honey_cake",
        helper="goat",
        tool="travel_brush",
        name="Rune",
        gender="boy",
        parent="father",
        trait="stubborn",
        seed=4,
    ),
    StoryParams(
        treat="berry_taffy",
        helper="pony",
        tool="full_kit",
        name="Freya",
        gender="girl",
        parent="mother",
        trait="careful",
        seed=5,
    ),
]


ASP_RULES = r"""
valid(Treat, Helper, Tool) :- treat(Treat), helper(Helper), tool(Tool),
                              stickiness(Treat, S), power(Tool, P), P >= S,
                              capacity(Helper, C), weight(Tool, W), C >= W.

quick_outcome :- chosen_trait(T), listening_trait(T).
quick_outcome :- chosen_helper(H), beloved_helper(H).
outcome(quick) :- quick_outcome.
outcome(pause) :- not quick_outcome.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        lines.append(asp.fact("stickiness", treat_id, treat.stickiness))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("capacity", helper_id, helper.capacity))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        lines.append(asp.fact("weight", tool_id, tool.weight))
    for trait in sorted(LISTENING_TRAITS):
        lines.append(asp.fact("listening_trait", trait))
    for helper_id in sorted(BELOVED_HELPERS):
        lines.append(asp.fact("beloved_helper", helper_id))
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
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

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
        description="Story world sketch: a little viking, a hygienist, and a fetch helper."
    )
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.helper and args.tool:
        treat = TREATS[args.treat]
        helper = HELPERS[args.helper]
        tool = TOOLS[args.tool]
        if not (tool_can_help(treat, tool) and helper_can_fetch(helper, tool)):
            raise StoryError(explain_rejection(treat, helper, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.treat is None or combo[0] == args.treat)
        and (args.helper is None or combo[1] == args.helper)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treat_id, helper_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        treat=treat_id,
        helper=helper_id,
        tool=tool_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def _validate_params(params: StoryParams) -> None:
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")
    treat = TREATS[params.treat]
    helper = HELPERS[params.helper]
    tool = TOOLS[params.tool]
    if not (tool_can_help(treat, tool) and helper_can_fetch(helper, tool)):
        raise StoryError(explain_rejection(treat, helper, tool))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        treat=TREATS[params.treat],
        fetcher=HELPERS[params.helper],
        tool=TOOLS[params.tool],
        hero_name=params.name,
        hero_gender=params.gender,
        trait=params.trait,
        parent_type=params.parent,
    )
    world.get("hero").attrs["display_name"] = params.name
    world.get("helper").attrs["tags"] = list(HELPERS[params.helper].tags)
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.name),
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
        print(f"{len(combos)} compatible (treat, helper, tool) combos:\n")
        for treat, helper, tool in combos:
            print(f"  {treat:12} {helper:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.treat} with {p.helper} fetching {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
