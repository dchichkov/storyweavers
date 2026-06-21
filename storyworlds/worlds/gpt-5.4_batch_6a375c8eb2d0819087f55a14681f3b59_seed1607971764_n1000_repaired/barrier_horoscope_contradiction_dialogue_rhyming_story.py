#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/barrier_horoscope_contradiction_dialogue_rhyming_story.py
====================================================================================

A standalone storyworld for a tiny rhyming domain: a child reads a silly
horoscope, wants to cross a barrier to get a better look at something lovely,
hears a grown-up point out the contradiction, and learns to choose the safe way.

The world model drives the prose:
- a place has a blocked sight and a hidden hazard beyond a barrier
- a horoscope makes a tempting promise
- a sign and helper introduce the contradiction
- the child either listens at once or pushes at the barrier first
- a safe aid solves the same need without crossing the barrier

The rendered story uses dialogue and a gentle rhyming style.

Run it
------
    python storyworlds/worlds/gpt-5.4/barrier_horoscope_contradiction_dialogue_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/barrier_horoscope_contradiction_dialogue_rhyming_story.py --place pier --barrier rope
    python storyworlds/worlds/gpt-5.4/barrier_horoscope_contradiction_dialogue_rhyming_story.py --aid kite
    python storyworlds/worlds/gpt-5.4/barrier_horoscope_contradiction_dialogue_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/barrier_horoscope_contradiction_dialogue_rhyming_story.py --verify
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
SENSE_MIN = 2
BOLD_INIT = 5.0
CAREFUL_TRAITS = {"careful", "thoughtful", "patient", "steady"}


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
    tags: set[str] = field(default_factory=set)

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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    intro: str
    hidden_view: str
    risky_ground: str
    sign_text: str
    hazard: str
    hazard_spread: int
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
class BarrierCfg:
    id: str
    label: str
    phrase: str
    verb: str
    strength: int
    warning: str
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
class HoroscopeCfg:
    id: str
    title: str
    promise: str
    dare: str
    contradiction_wording: str
    boldness: int
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
class Aid:
    id: str
    label: str
    phrase: str
    action: str
    solves: set[str]
    sense: int
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


def _r_barrier_push(world: World) -> list[str]:
    child = world.get("child")
    barrier = world.get("barrier")
    if child.meters["pushing_barrier"] < THRESHOLD:
        return []
    sig = ("push",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    if barrier.attrs["strength"] <= 1:
        child.meters["past_barrier"] += 1
        return ["__past_barrier__"]
    barrier.meters["holding"] += 1
    return ["__held__"]


def _r_hazard(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["past_barrier"] < THRESHOLD:
        return []
    sig = ("hazard",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place = world.get("place")
    child.meters["risk"] += 1
    child.memes["fear"] += 1
    place.meters["danger"] += 1
    return ["__danger__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="barrier_push", tag="physical", apply=_r_barrier_push),
    Rule(name="hazard", tag="physical", apply=_r_hazard),
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
            if not s.startswith("__"):
                world.say(s)
    return produced


def compatible_aids(place: Place) -> list[str]:
    return sorted(
        aid_id for aid_id, aid in AIDS.items()
        if place.id in aid.solves and aid.sense >= SENSE_MIN
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        if not compatible_aids(place):
            continue
        for horoscope_id in HOROSCOPES:
            for barrier_id in BARRIERS:
                combos.append((place_id, horoscope_id, barrier_id))
    return combos


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_listen(trait: str, trust: int, horoscope: HoroscopeCfg) -> bool:
    care = initial_care(trait)
    pressure = BOLD_INIT + horoscope.boldness
    support = care + (trust / 2.0)
    return support > pressure


def predict_consequence(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["pushing_barrier"] += 1
    propagate(sim, narrate=False)
    return {
        "past_barrier": sim.get("child").meters["past_barrier"] >= THRESHOLD,
        "risk": sim.get("child").meters["risk"] >= THRESHOLD,
        "danger": sim.get("place").meters["danger"],
    }


def opening(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"At {place.label}, where bright winds loved to whirl, "
        f"{child.id} skipped beside {helper.id} with a hopeful twirl."
    )
    world.say(
        f"{place.intro} Beyond a barrier there gleamed {place.hidden_view}, "
        f"the kind that made a waiting child want just a closer view."
    )


def find_horoscope(world: World, child: Entity, horoscope: HoroscopeCfg) -> None:
    child.memes["tempted"] += 1
    world.say(
        f"A crinkly horoscope page came fluttering from the sky. "
        f'"{horoscope.title}," read {child.id}, "today your luck will fly!"'
    )
    world.say(
        f'"{horoscope.promise}" {child.id} read aloud. '
        f'"{horoscope.dare}," {child.pronoun()} said, half bold and half too proud.'
    )


def notice_barrier(world: World, child: Entity, helper: Entity,
                   barrier: BarrierCfg, place: Place) -> None:
    world.say(
        f"But there across the path was {barrier.phrase}, tied neat and bright and fair, "
        f"and next to it a sign that said, \"{place.sign_text}\" with care."
    )
    world.say(
        f'"That {barrier.label} is there for a reason," said {helper.id}. '
        f'"Past it lies {place.risky_ground}, and {place.hazard} can be hid."'
    )


def discuss_contradiction(world: World, child: Entity, helper: Entity,
                          horoscope: HoroscopeCfg) -> None:
    pred = predict_consequence(world)
    world.facts["predicted_risk"] = pred["risk"]
    child.memes["confused"] += 1
    helper.memes["calm"] += 1
    world.say(
        f'"But my horoscope says luck is waiting if I hurry through!" said {child.id}.'
    )
    second = (
        f"The helper shook {helper.pronoun('possessive')} head and spoke in steady diction: "
        f'"When paper says one thing and safety says another, that is contradiction."'
    )
    if pred["risk"]:
        second += (
            f" \"Good luck is not a dare to duck past rules that guard {place_name(world)}.\""
        )
    world.say(second)


def place_name(world: World) -> str:
    return world.get("place").label


def choose_heed(world: World, child: Entity, helper: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["listened"] += 1
    world.say(
        f'{child.id} looked at the sign, then up at {helper.id}\'s face. '
        f'"You\'re right," said {child.pronoun()}, "slow thinking fits this place."'
    )


def try_barrier(world: World, child: Entity, barrier: BarrierCfg, place: Place) -> None:
    child.meters["pushing_barrier"] += 1
    out = propagate(world, narrate=False)
    if "__past_barrier__" in out:
        world.say(
            f'But temptation beat patience for one tiny blink of time. '
            f'{child.id} slipped past the {barrier.label} with a quick and foolish climb.'
        )
        world.say(
            f"At once {child.pronoun('possessive')} shoe found {place.risky_ground}, slick and thin and cold, "
            f"and the day that had felt shiny suddenly felt too bold."
        )
    else:
        world.say(
            f'For one small second {child.id} gave the {barrier.label} a {barrier.verb} and tugged. '
            f'It held fast, and {child.pronoun()} felt {child.pronoun("possessive")} little stomach hug.'
        )
        world.say(
            f'"This barrier is stronger than my hurry," {child.pronoun()} said with a sigh, '
            f"as the sign and all its meaning seemed to stand up tall nearby."
        )


def rescue(world: World, child: Entity, helper: Entity, barrier: BarrierCfg, place: Place) -> None:
    if child.meters["past_barrier"] < THRESHOLD:
        child.memes["relief"] += 1
        return
    child.meters["past_barrier"] = 0.0
    world.get("place").meters["danger"] = 0.0
    child.meters["risk"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f'{helper.id} reached out calmly. "{barrier.warning}," {helper.pronoun()} said. '
        f'{helper.pronoun().capitalize()} guided {child.id} back from {place.risky_ground} to the safe side of the rail.'
    )


def safe_solution(world: World, child: Entity, helper: Entity, aid: Aid, place: Place) -> None:
    child.memes["joy"] += 1
    child.memes["learned"] += 1
    world.say(
        f'Then {helper.id} smiled and said, "We do not need to race. '
        f'We can {aid.action} and still enjoy this place."'
    )
    world.say(
        f"Soon there was {aid.phrase}, and from the safe side all looked bright; "
        f"{child.id} could see {place.hidden_view}, clear as a silver light."
    )
    world.say(
        f'"The horoscope was wrong about the shortcut," laughed {child.id} at last. '
        f'"But careful steps made better luck, and better luck can last."'
    )


def ending_image(world: World, child: Entity, helper: Entity, barrier: BarrierCfg) -> None:
    world.say(
        f"Beside the quiet {barrier.label}, with evening soft and starry, "
        f"{child.id} stayed close to {helper.id} and felt no need to hurry."
    )


def tell(place: Place, horoscope: HoroscopeCfg, barrier: BarrierCfg, aid: Aid,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Dad", helper_gender: str = "father",
         trait: str = "careful", trust: int = 7) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        label="the helper",
        attrs={},
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        attrs={"hazard": place.hazard, "risky_ground": place.risky_ground},
        tags=set(place.tags),
    ))
    barrier_ent = world.add(Entity(
        id="barrier",
        kind="thing",
        type="barrier",
        label=barrier.label,
        attrs={"strength": barrier.strength},
        tags=set(barrier.tags),
    ))
    world.facts.update(
        place_cfg=place,
        horoscope_cfg=horoscope,
        barrier_cfg=barrier,
        aid_cfg=aid,
        child=child,
        helper=helper,
        attempted=False,
    )
    child.memes["trust"] = float(trust)
    child.memes["care"] = initial_care(trait)
    child.memes["bold"] = BOLD_INIT

    opening(world, child, helper, place)
    world.para()
    find_horoscope(world, child, horoscope)
    notice_barrier(world, child, helper, barrier, place)
    discuss_contradiction(world, child, helper, horoscope)

    listened = would_listen(trait, trust, horoscope)
    world.facts["listened_first"] = listened

    world.para()
    if listened:
        choose_heed(world, child, helper)
    else:
        world.facts["attempted"] = True
        try_barrier(world, child, barrier, place)
        rescue(world, child, helper, barrier, place)

    safe_solution(world, child, helper, aid, place)
    ending_image(world, child, helper, barrier)

    outcome = "heeded" if listened else "redirected"
    world.facts.update(
        outcome=outcome,
        contradiction=True,
        risk_seen=world.get("child").memes["relief"] >= THRESHOLD and not listened,
        aid_used=aid.id,
    )
    return world


PLACES = {
    "pier": Place(
        id="pier",
        label="the little pier",
        intro="Gulls called over the boards, and the water kept a shimmery tune.",
        hidden_view="the moon's path on the water",
        risky_ground="the wet edge of the pier",
        sign_text="Please stay behind the safety line",
        hazard="slippery boards",
        hazard_spread=2,
        tags={"water", "moon"},
    ),
    "garden": Place(
        id="garden",
        label="the town garden",
        intro="Rows of tulips leaned like lanterns, and a glasshouse blinked with dew.",
        hidden_view="a nest tucked high in the ivy arch",
        risky_ground="the muddy flower bed",
        sign_text="Please stay behind the garden fence",
        hazard="soft muddy ground",
        hazard_spread=1,
        tags={"garden", "birds"},
    ),
    "hill": Place(
        id="hill",
        label="the kite hill",
        intro="The grass rolled down in windy folds, and clouds sailed white and slow.",
        hidden_view="a rainbow resting over the town",
        risky_ground="the crumbly slope edge",
        sign_text="Please stay behind the rope line",
        hazard="loose stones",
        hazard_spread=2,
        tags={"rainbow", "wind"},
    ),
}

BARRIERS = {
    "rope": BarrierCfg(
        id="rope",
        label="rope barrier",
        phrase="a rope barrier",
        verb="careful pull",
        strength=2,
        warning="Easy now",
        tags={"barrier"},
    ),
    "gate": BarrierCfg(
        id="gate",
        label="small gate",
        phrase="a small gate with a bright red latch",
        verb="hard push",
        strength=2,
        warning="Back to me, please",
        tags={"barrier"},
    ),
    "hedge": BarrierCfg(
        id="hedge",
        label="low hedge",
        phrase="a low hedge with a wooden sign beside it",
        verb="squeeze",
        strength=1,
        warning="Stop there, little feet",
        tags={"barrier"},
    ),
}

HOROSCOPES = {
    "comet": HoroscopeCfg(
        id="comet",
        title="Horoscope for Sparkly Souls",
        promise="A shining surprise will smile on the brave today",
        dare="Maybe I should hurry before the magic slips away",
        contradiction_wording="brave",
        boldness=2,
        tags={"horoscope"},
    ),
    "lucky_step": HoroscopeCfg(
        id="lucky_step",
        title="Horoscope for Lucky Toes",
        promise="One extra step will bring a perfect view today",
        dare="Maybe one quick step past the line would help me see",
        contradiction_wording="one extra step",
        boldness=2,
        tags={"horoscope"},
    ),
    "secret_path": HoroscopeCfg(
        id="secret_path",
        title="Horoscope for Secret Finders",
        promise="A hidden path may lead to joy today",
        dare="Maybe the best surprise is just beyond that line",
        contradiction_wording="hidden path",
        boldness=1,
        tags={"horoscope"},
    ),
}

AIDS = {
    "stepstool": Aid(
        id="stepstool",
        label="step stool",
        phrase="a sturdy little step stool",
        action="stand on the step stool",
        solves={"pier", "garden"},
        sense=3,
        tags={"stool", "safe_view"},
    ),
    "binoculars": Aid(
        id="binoculars",
        label="binoculars",
        phrase="a pair of bright blue binoculars",
        action="look through the binoculars",
        solves={"pier", "garden", "hill"},
        sense=3,
        tags={"binoculars", "safe_view"},
    ),
    "blanket_spot": Aid(
        id="blanket_spot",
        label="picnic blanket",
        phrase="a picnic blanket on the safe grass",
        action="sit on the blanket and watch from there",
        solves={"hill"},
        sense=2,
        tags={"blanket", "safe_view"},
    ),
    "kite": Aid(
        id="kite",
        label="kite",
        phrase="a red kite",
        action="fly the kite",
        solves={"hill"},
        sense=1,
        tags={"kite"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ruby", "Zoe"]
BOY_NAMES = ["Owen", "Max", "Finn", "Leo", "Milo", "Sam"]
TRAITS = ["careful", "thoughtful", "patient", "steady", "curious", "bold"]


@dataclass
class StoryParams:
    place: str
    horoscope: str
    barrier: str
    aid: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    trust: int
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
    "barrier": [
        (
            "What is a barrier?",
            "A barrier is something that marks a place you should not cross. It helps keep people away from danger."
        )
    ],
    "horoscope": [
        (
            "What is a horoscope?",
            "A horoscope is a little message that claims to tell what might happen. It can be fun to read, but it should not be used instead of good safety rules."
        )
    ],
    "contradiction": [
        (
            "What is a contradiction?",
            "A contradiction is when two ideas do not fit together. If one thing says 'go' and another good reason says 'stop,' you need to think carefully."
        )
    ],
    "binoculars": [
        (
            "What do binoculars do?",
            "Binoculars help your eyes see things that are far away. They let you get a better view without walking closer."
        )
    ],
    "stool": [
        (
            "Why can a step stool be helpful?",
            "A step stool can help a small person see a little higher. It is helpful when a grown-up places it in a safe spot."
        )
    ],
    "safe_view": [
        (
            "Why is it smart to find a safe way to look at something?",
            "A safe way lets you enjoy the view without going near the risky place. Good ideas solve the problem and protect your body at the same time."
        )
    ],
}
KNOWLEDGE_ORDER = ["barrier", "horoscope", "contradiction", "binoculars", "stool", "safe_view"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place_cfg"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "barrier," "horoscope," and "contradiction," and uses dialogue.',
        f"Tell a gentle story where {child.id} reads a horoscope, wants to cross a barrier at {place.label}, and a calm grown-up explains the contradiction.",
        f"Write a dialogue-rich rhyming story about a child choosing a safe way to get a better view instead of slipping past a barrier.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    barrier = f["barrier_cfg"]
    horoscope = f["horoscope_cfg"]
    aid = f["aid_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.id} at {place.label}. {child.id} wanted a closer look at {place.hidden_view}."
        ),
        (
            "Why did the child want to go past the barrier?",
            f"{child.id} read a horoscope that made crossing sound lucky and exciting. The promise tugged at {child.pronoun('possessive')} feelings because {child.pronoun()} wanted a better view right away."
        ),
        (
            "What was the contradiction in the story?",
            f"The horoscope pushed {child.id} toward hurrying forward, but the sign and {helper.id} warned that the place past the barrier was unsafe. That contradiction mattered because one message was playful, while the other was there to protect {child.pronoun('object')}."
        ),
    ]
    if outcome == "heeded":
        qa.append(
            (
                f"How did {child.id} solve the problem?",
                f"{child.id} listened before crossing and used {aid.phrase} instead. That gave {child.pronoun('object')} a safe view without going near {place.risky_ground}."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child.id} tried the barrier?",
                f"{child.id} tested the {barrier.label} and the moment turned scary instead of lucky. The danger showed why the sign was there, and {helper.id} calmly brought {child.pronoun('object')} back to safety."
            )
        )
        qa.append(
            (
                f"What changed at the end?",
                f"At first {child.id} treated the horoscope like a dare, but later {child.pronoun()} trusted safety more than the shortcut. Then {child.pronoun()} used {aid.phrase} and saw the beautiful view the safe way."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"barrier", "horoscope", "contradiction", "safe_view"}
    aid = f["aid_cfg"]
    if "binoculars" in aid.tags:
        tags.add("binoculars")
    if "stool" in aid.tags:
        tags.add("stool")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pier",
        horoscope="comet",
        barrier="rope",
        aid="binoculars",
        child_name="Mina",
        child_gender="girl",
        helper_name="Dad",
        helper_gender="father",
        trait="careful",
        trust=8,
    ),
    StoryParams(
        place="garden",
        horoscope="lucky_step",
        barrier="hedge",
        aid="stepstool",
        child_name="Owen",
        child_gender="boy",
        helper_name="Mom",
        helper_gender="mother",
        trait="curious",
        trust=4,
    ),
    StoryParams(
        place="hill",
        horoscope="secret_path",
        barrier="gate",
        aid="blanket_spot",
        child_name="Ruby",
        child_gender="girl",
        helper_name="Dad",
        helper_gender="father",
        trait="steady",
        trust=7,
    ),
    StoryParams(
        place="pier",
        horoscope="lucky_step",
        barrier="hedge",
        aid="stepstool",
        child_name="Finn",
        child_gender="boy",
        helper_name="Mom",
        helper_gender="mother",
        trait="bold",
        trust=3,
    ),
]


def explain_aid(aid_id: str, place_id: str) -> str:
    aid = AIDS[aid_id]
    if aid.sense < SENSE_MIN:
        return (
            f"(Refusing aid '{aid_id}': it is too weak as a safety fix here. "
            f"Choose a safer view helper like {', '.join(compatible_aids(PLACES[place_id]))}.)"
        )
    return (
        f"(No story: {aid.label} does not solve the viewing problem at {PLACES[place_id].label}. "
        f"Pick one of: {', '.join(compatible_aids(PLACES[place_id]))}.)"
    )


def explain_combo(place_id: str) -> str:
    return f"(No story: {PLACES[place_id].label} needs a sensible safe-view aid, but none is available.)"


ASP_RULES = r"""
place_has_fix(P) :- place(P), aid(A), solves(A,P), sense(A,S), sense_min(M), S >= M.
valid(P,H,B) :- place(P), horoscope(H), barrier(B), place_has_fix(P).

careful(T) :- trait(T), careful_trait(T).
support(C + Tr) :- care_value(C), trust_half(Tr).
care_value(5) :- trait(T), careful(T).
care_value(3) :- trait(T), not careful(T).
trust_half(T / 2) :- trust(T).
pressure(B + HB) :- bold_init(B), chosen_horoscope(H), horoscope_bold(H,HB).
listens_first :- support(S), pressure(P), S > P.

outcome(heeded) :- listens_first.
outcome(redirected) :- not listens_first.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for horoscope_id, horoscope in HOROSCOPES.items():
        lines.append(asp.fact("horoscope", horoscope_id))
        lines.append(asp.fact("horoscope_bold", horoscope_id, horoscope.boldness))
    for barrier_id in BARRIERS:
        lines.append(asp.fact("barrier", barrier_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        for place_id in sorted(aid.solves):
            lines.append(asp.fact("solves", aid_id, place_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bold_init", int(BOLD_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_horoscope", params.horoscope),
        asp.fact("trait", params.trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    horoscope = HOROSCOPES[params.horoscope]
    return "heeded" if would_listen(params.trait, params.trust, horoscope) else "redirected"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a horoscope, a barrier, and a safe contradiction lesson."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--horoscope", choices=HOROSCOPES)
    ap.add_argument("--barrier", choices=BARRIERS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
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


def _pick_child(rng: random.Random, gender: Optional[str], name: Optional[str]) -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    if name:
        return name, chosen_gender
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    return rng.choice(pool), chosen_gender


def _helper_name(gender: str) -> str:
    return "Mom" if gender == "mother" else "Dad"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and not compatible_aids(PLACES[args.place]):
        raise StoryError(explain_combo(args.place))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.horoscope is None or combo[1] == args.horoscope)
        and (args.barrier is None or combo[2] == args.barrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, horoscope_id, barrier_id = rng.choice(sorted(combos))
    valid_aids = compatible_aids(PLACES[place_id])

    if args.aid:
        if args.aid not in valid_aids:
            raise StoryError(explain_aid(args.aid, place_id))
        aid_id = args.aid
    else:
        aid_id = rng.choice(valid_aids)

    child_name, child_gender = _pick_child(rng, args.child_gender, args.child_name)
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    helper_name = _helper_name(helper_gender)
    trait = args.trait or rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(0, 10)

    return StoryParams(
        place=place_id,
        horoscope=horoscope_id,
        barrier=barrier_id,
        aid=aid_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.horoscope not in HOROSCOPES:
        raise StoryError(f"(Unknown horoscope: {params.horoscope})")
    if params.barrier not in BARRIERS:
        raise StoryError(f"(Unknown barrier: {params.barrier})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.aid not in compatible_aids(PLACES[params.place]):
        raise StoryError(explain_aid(params.aid, params.place))

    world = tell(
        place=PLACES[params.place],
        horoscope=HOROSCOPES[params.horoscope],
        barrier=BARRIERS[params.barrier],
        aid=AIDS[params.aid],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        trait=params.trait,
        trust=params.trust,
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
        print(f"{len(combos)} compatible (place, horoscope, barrier) combos:\n")
        for place_id, horoscope_id, barrier_id in combos:
            aids = ", ".join(compatible_aids(PLACES[place_id]))
            print(f"  {place_id:8} {horoscope_id:11} {barrier_id:7}  [aids: {aids}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.place} / {p.horoscope} / {p.barrier} "
                f"({outcome_of(p)}, aid={p.aid})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
