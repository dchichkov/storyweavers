#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kaleidoscope_problem_solving_kindness_heartwarming.py
================================================================================

A standalone story world about a child using kindness and simple problem solving
to help someone see the bright patterns inside a kaleidoscope. The central
constraint is concrete and physical: a kaleidoscope needs enough light. Some
solutions truly brighten the place; others do not, and the world refuses them.

Run it
------
    python storyworlds/worlds/gpt-5.4/kaleidoscope_problem_solving_kindness_heartwarming.py
    python storyworlds/worlds/gpt-5.4/kaleidoscope_problem_solving_kindness_heartwarming.py --place blanket_fort --solution lamp
    python storyworlds/worlds/gpt-5.4/kaleidoscope_problem_solving_kindness_heartwarming.py --place hallway_bench --solution open_curtain
    python storyworlds/worlds/gpt-5.4/kaleidoscope_problem_solving_kindness_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/kaleidoscope_problem_solving_kindness_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/kaleidoscope_problem_solving_kindness_heartwarming.py --verify
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
NEEDED_LIGHT = 2
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    phrase: str
    nearby_bright_spot: str
    base_light: int
    has_curtain: bool = False
    has_lamp: bool = False
    has_sunbeam: bool = False
    movable: bool = False
    warm_detail: str = ""
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
class Solution:
    id: str
    sense: int
    gain: int
    text: str
    qa_text: str
    needs_curtain: bool = False
    needs_lamp: bool = False
    needs_sunbeam: bool = False
    needs_movable: bool = False
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
class Recipient:
    id: str
    relation: str
    title: str
    sad_reason: str
    comfort_line: str
    type: str
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
class Mood:
    id: str
    opening: str
    sign: str
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


def _r_dim_view(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("attempted_view"):
        return out
    place = world.get("place")
    tube = world.get("kaleidoscope")
    if place.meters["light"] >= NEEDED_LIGHT:
        return out
    sig = ("dim_view",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tube.meters["blurred"] += 1
    for eid in ("hero", "recipient"):
        world.get(eid).memes["disappointed"] += 1
    world.facts["saw_colors"] = False
    out.append("__dim__")
    return out


def _r_bright_view(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("attempted_view"):
        return out
    place = world.get("place")
    tube = world.get("kaleidoscope")
    if place.meters["light"] < NEEDED_LIGHT:
        return out
    sig = ("bright_view",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tube.meters["sparkle"] += 1
    tube.meters["colors_seen"] += 1
    for eid in ("hero", "recipient"):
        world.get(eid).memes["joy"] += 1
        world.get(eid).memes["wonder"] += 1
    world.facts["saw_colors"] = True
    out.append("__bright__")
    return out


def _r_kind_share(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("shared_first_turn"):
        return out
    recipient = world.get("recipient")
    if recipient.memes["sad"] < THRESHOLD:
        return out
    sig = ("kind_share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["kindness"] += 1
    recipient.memes["comfort"] += 1
    recipient.memes["sad"] = 0.0
    out.append("__comfort__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="dim_view", tag="physical", apply=_r_dim_view),
    Rule(name="bright_view", tag="physical", apply=_r_bright_view),
    Rule(name="kind_share", tag="social", apply=_r_kind_share),
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


def solution_works(place: Place, solution: Solution) -> bool:
    if solution.sense < SENSE_MIN:
        return False
    if solution.needs_curtain and not place.has_curtain:
        return False
    if solution.needs_lamp and not place.has_lamp:
        return False
    if solution.needs_sunbeam and not place.has_sunbeam:
        return False
    if solution.needs_movable and not place.movable:
        return False
    return place.base_light + solution.gain >= NEEDED_LIGHT


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for solution_id, solution in SOLUTIONS.items():
            if solution_works(place, solution):
                combos.append((place_id, solution_id))
    return combos


def predict_after_solution(world: World, solution: Solution) -> dict:
    sim = world.copy()
    sim.get("place").meters["light"] += solution.gain
    sim.facts["attempted_view"] = True
    propagate(sim, narrate=False)
    return {
        "light": sim.get("place").meters["light"],
        "saw_colors": bool(sim.facts.get("saw_colors")),
    }


def introduce(world: World, hero: Entity, recipient: Entity, mood: Mood) -> None:
    hero.memes["care"] += 1
    recipient.memes["sad"] += 1
    world.say(
        f"{hero.id} carried a small kaleidoscope in {hero.pronoun('possessive')} pocket. "
        f"{mood.opening}"
    )
    world.say(
        f"{recipient.id}, {recipient.attrs['title']}, {mood.sign} {recipient.comfort_line}"
    )


def arrive(world: World, hero: Entity, recipient: Entity, place: Place) -> None:
    world.say(
        f"After lunch they sat together in {place.phrase}. {place.warm_detail}"
    )
    world.say(
        f"{hero.id} remembered the kaleidoscope and thought it might make {recipient.id} smile."
    )


def offer(world: World, hero: Entity, recipient: Entity) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f'"Would you like to look first?" {hero.id} asked. '
        f'{hero.pronoun().capitalize()} held the kaleidoscope out with both hands.'
    )
    world.facts["shared_first_turn"] = True
    propagate(world, narrate=False)


def first_try(world: World, hero: Entity, recipient: Entity, place: Place) -> None:
    world.facts["attempted_view"] = True
    propagate(world, narrate=False)
    world.say(
        f"{recipient.id} lifted the kaleidoscope to {recipient.pronoun('possessive')} eye and turned it slowly."
    )
    if world.facts.get("saw_colors"):
        world.say("At once, bright little shapes opened like a paper flower.")
        return
    world.say(
        f"But {place.label} was too dim. Inside the tube there was only a gray blur instead of dancing colors."
    )
    world.say(
        f"{recipient.id}'s face fell, and {hero.id} felt a pinch in {hero.pronoun('possessive')} heart."
    )


def think(world: World, hero: Entity, recipient: Entity, place: Place, solution: Solution) -> None:
    pred = predict_after_solution(world, solution)
    world.facts["predicted_light"] = pred["light"]
    world.facts["predicted_success"] = pred["saw_colors"]
    hero.memes["problem_solving"] += 1
    recipient.memes["hope"] += 1
    world.say("For a moment, neither of them spoke.")
    world.say(
        f"Then {hero.id} looked around {place.label}, thinking about what the kaleidoscope needed."
    )
    world.say(
        f'"It needs more light," {hero.pronoun()} said softly. "Maybe we can fix that together."'
    )


def solve(world: World, hero: Entity, recipient: Entity, place_cfg: Place, solution: Solution) -> None:
    place = world.get("place")
    place.meters["light"] += solution.gain
    world.facts["attempted_view"] = False
    world.say(solution.text.format(hero=hero.id, recipient=recipient.id, spot=place_cfg.nearby_bright_spot))
    place.attrs["solution_used"] = solution.id
    hero.memes["hope"] += 1
    recipient.memes["hope"] += 1


def second_try(world: World, hero: Entity, recipient: Entity) -> None:
    world.facts["attempted_view"] = True
    propagate(world, narrate=False)
    world.say(
        f"This time {recipient.id} peered through the kaleidoscope again."
    )
    if not world.facts.get("saw_colors"):
        raise StoryError("(Story bug: chosen solution did not provide enough light.)")
    world.say(
        "Red, blue, gold, and green clicked into place and spun into tiny shining stars."
    )
    world.say(
        f"{recipient.id} gave a surprised little laugh, and {hero.id} laughed too."
    )


def closing(world: World, hero: Entity, recipient: Entity, mood: Mood, place: Place) -> None:
    hero.memes["joy"] += 1
    recipient.memes["joy"] += 1
    world.say(
        f'After that they took turns with the kaleidoscope, each twist making a brand-new pattern.'
    )
    world.say(
        f"{mood.ending_image} In {place.label}, the light seemed kinder now because they had made it together."
    )


def tell(
    place_cfg: Place,
    solution_cfg: Solution,
    recipient_cfg: Recipient,
    mood_cfg: Mood,
    hero_name: str = "Mia",
    hero_type: str = "girl",
    recipient_name: str = "Ben",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    recipient = world.add(
        Entity(
            id="recipient",
            kind="character",
            type=recipient_cfg.type,
            label=recipient_name,
            role="recipient",
            attrs={"title": recipient_cfg.title, "relation": recipient_cfg.relation},
        )
    )
    place = world.add(Entity(id="place", type="place", label=place_cfg.label))
    place.meters["light"] = float(place_cfg.base_light)
    kaleidoscope = world.add(Entity(id="kaleidoscope", type="toy", label="kaleidoscope"))
    world.facts["attempted_view"] = False
    world.facts["shared_first_turn"] = False
    world.facts["saw_colors"] = False
    world.facts["solution"] = solution_cfg
    world.facts["place_cfg"] = place_cfg
    world.facts["recipient_cfg"] = recipient_cfg
    world.facts["mood_cfg"] = mood_cfg

    introduce(world, hero, recipient, mood_cfg)
    arrive(world, hero, recipient, place_cfg)

    world.para()
    offer(world, hero, recipient)
    first_try(world, hero, recipient, place_cfg)

    world.para()
    think(world, hero, recipient, place_cfg, solution_cfg)
    solve(world, hero, recipient, place_cfg, solution_cfg)
    second_try(world, hero, recipient)

    world.para()
    closing(world, hero, recipient, mood_cfg, place_cfg)

    world.facts.update(
        hero=hero,
        recipient=recipient,
        place=place,
        kaleidoscope=kaleidoscope,
        saw_colors=bool(world.facts.get("saw_colors")),
        comforted=recipient.memes["comfort"] >= THRESHOLD,
        light=place.meters["light"],
    )
    return world


PLACES = {
    "window_seat": Place(
        id="window_seat",
        label="the window seat",
        phrase="the little window seat by the front room",
        nearby_bright_spot="the sunny edge of the cushion",
        base_light=1,
        has_curtain=True,
        has_lamp=False,
        has_sunbeam=True,
        movable=True,
        warm_detail="A sleepy stripe of afternoon light rested near the glass, but the curtain was half closed.",
        tags={"window", "light"},
    ),
    "blanket_fort": Place(
        id="blanket_fort",
        label="the blanket fort",
        phrase="a blanket fort under the table",
        nearby_bright_spot="the open patch by the fort door",
        base_light=0,
        has_curtain=False,
        has_lamp=True,
        has_sunbeam=False,
        movable=True,
        warm_detail="The blankets made a cozy roof, but they kept most of the light outside.",
        tags={"fort", "light"},
    ),
    "hallway_bench": Place(
        id="hallway_bench",
        label="the hallway bench",
        phrase="the quiet hallway bench near the coat hooks",
        nearby_bright_spot="the bright kitchen doorway",
        base_light=1,
        has_curtain=False,
        has_lamp=False,
        has_sunbeam=False,
        movable=True,
        warm_detail="It was a peaceful place to sit, though the hallway only caught a thin wash of light.",
        tags={"hallway", "light"},
    ),
    "attic_corner": Place(
        id="attic_corner",
        label="the attic corner",
        phrase="the attic corner beside the old trunk",
        nearby_bright_spot="the square of sun on the floorboards",
        base_light=0,
        has_curtain=False,
        has_lamp=True,
        has_sunbeam=True,
        movable=True,
        warm_detail="Dust floated softly there, and one square of sunshine lay a few steps away.",
        tags={"attic", "light"},
    ),
}

SOLUTIONS = {
    "open_curtain": Solution(
        id="open_curtain",
        sense=3,
        gain=2,
        text="{hero} slipped over to the curtain and pulled it wide. Warm daylight poured across the seat.",
        qa_text="pulled the curtain open to let in more daylight",
        needs_curtain=True,
        tags={"curtain", "daylight"},
    ),
    "lamp": Solution(
        id="lamp",
        sense=3,
        gain=2,
        text="{hero} clicked on the nearby lamp, and a gentle pool of light spread over their knees.",
        qa_text="turned on a lamp so the kaleidoscope had enough light",
        needs_lamp=True,
        tags={"lamp", "light"},
    ),
    "move_to_bright_spot": Solution(
        id="move_to_bright_spot",
        sense=3,
        gain=1,
        text='{hero} scooted close to {spot}. "Let\'s try right here," {hero} said.',
        qa_text="moved with the kaleidoscope to a brighter spot",
        needs_movable=True,
        tags={"window", "light"},
    ),
    "catch_sunbeam": Solution(
        id="catch_sunbeam",
        sense=2,
        gain=2,
        text="{hero} carried the kaleidoscope to the sunbeam and tilted it until the light slipped neatly through.",
        qa_text="brought the kaleidoscope into a sunbeam",
        needs_sunbeam=True,
        tags={"sunbeam", "daylight"},
    ),
    "shake_harder": Solution(
        id="shake_harder",
        sense=1,
        gain=0,
        text="{hero} shook the kaleidoscope harder, but that only made the gray blur wobble.",
        qa_text="shook the kaleidoscope harder",
        tags={"mistake"},
    ),
}

RECIPIENTS = {
    "brother": Recipient(
        id="brother",
        relation="little brother",
        title="her little brother",
        sad_reason="had lost a block tower that morning",
        comfort_line="still looked disappointed after he had lost a block tower that morning.",
        type="boy",
        tags={"family"},
    ),
    "sister": Recipient(
        id="sister",
        relation="little sister",
        title="her little sister",
        sad_reason="had been left out of a game earlier",
        comfort_line="was quiet after being left out of a game earlier.",
        type="girl",
        tags={"family"},
    ),
    "friend": Recipient(
        id="friend",
        relation="new friend",
        title="a new friend from next door",
        sad_reason="felt shy in the new house",
        comfort_line="twisted the hem of a sleeve because the new house still felt strange.",
        type="girl",
        tags={"friendship"},
    ),
    "grandpa": Recipient(
        id="grandpa",
        relation="grandpa",
        title="her grandpa",
        sad_reason="was having a slow, tired day",
        comfort_line="was smiling a little, but his eyes looked tired today.",
        type="grandfather",
        tags={"family"},
    ),
}

MOODS = {
    "cheer_up": Mood(
        id="cheer_up",
        opening="That afternoon, someone close to her needed cheering up.",
        sign="",
        ending_image="Soon the room was full of soft laughter.",
        tags={"kindness"},
    ),
    "shy_day": Mood(
        id="shy_day",
        opening="It was one of those small, quiet days when kindness mattered a lot.",
        sign="",
        ending_image="By the end, the smiles between them felt bright and steady.",
        tags={"kindness"},
    ),
    "tired_day": Mood(
        id="tired_day",
        opening="The day felt gentle and slow, as if everyone needed a little extra care.",
        sign="",
        ending_image="The bright patterns kept turning, and so did the warm feeling in their hearts.",
        tags={"kindness"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella", "Anna", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Max", "Noah", "Finn", "Theo", "Sam", "Eli"]


@dataclass
class StoryParams:
    place: str
    solution: str
    recipient: str
    mood: str
    hero_name: str
    hero_gender: str
    recipient_name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    recipient = f["recipient"]
    place_cfg = f["place_cfg"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the word "kaleidoscope" and shows kindness solving a small problem.',
        f"Tell a gentle story where {hero.label} wants to cheer up {recipient.label} with a kaleidoscope, but {place_cfg.label} is too dim at first.",
        "Write a simple story in which a child notices what is wrong, thinks carefully, and makes enough light for a kaleidoscope to sparkle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    recipient = f["recipient"]
    place_cfg = f["place_cfg"]
    solution = f["solution"]
    recipient_cfg = f["recipient_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who wanted to be kind, and {recipient.label}, who needed cheering up. The story follows how they used a kaleidoscope together.",
        ),
        (
            f"Why did {hero.label} bring out the kaleidoscope?",
            f"{hero.label} noticed that {recipient.label} was sad because {recipient_cfg.sad_reason}. {hero.pronoun('subject').capitalize()} hoped the bright patterns inside the kaleidoscope would help {recipient.pronoun('object')} feel better.",
        ),
        (
            "What problem did they have at first?",
            f"The first try did not work because {place_cfg.label} was too dim. A kaleidoscope needs enough light, so they could only see a gray blur at first.",
        ),
        (
            f"How did {hero.label} solve the problem?",
            f"{hero.label} realized the kaleidoscope needed more light and {solution.qa_text}. That changed the place itself, so the colors could finally appear.",
        ),
        (
            f"How was {hero.label} kind?",
            f"{hero.label} offered {recipient.label} the first turn with the kaleidoscope instead of keeping it. That kind choice mattered because {recipient.label} was already having a hard day.",
        ),
        (
            "How did the story end?",
            f"The colors finally shone inside the kaleidoscope, and both of them laughed. The ending feels warm because a small problem was solved with care instead of giving up.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "light": [
        (
            "Why does a kaleidoscope need light?",
            "A kaleidoscope works by letting light bounce around inside it. Without enough light, the shapes inside look dull or hard to see."
        )
    ],
    "daylight": [
        (
            "What is daylight?",
            "Daylight is the natural light that comes from the sun during the day. It helps us see colors clearly."
        )
    ],
    "lamp": [
        (
            "What does a lamp do?",
            "A lamp makes light in a room. Turning one on can help you see things better when a place is dim."
        )
    ],
    "sunbeam": [
        (
            "What is a sunbeam?",
            "A sunbeam is a bright band of sunlight shining into a place. It can make colors look warmer and clearer."
        )
    ],
    "window": [
        (
            "Why does opening a curtain make a room brighter?",
            "Opening a curtain lets more daylight come through the window. More light can change a dim corner into a bright one."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help someone or comfort them. Even a small kind act can make another person feel less lonely."
        )
    ],
}
KNOWLEDGE_ORDER = ["kindness", "light", "daylight", "lamp", "sunbeam", "window"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"kindness", "light"}
    solution = world.facts["solution"]
    tags |= set(solution.tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="window_seat",
        solution="open_curtain",
        recipient="brother",
        mood="cheer_up",
        hero_name="Mia",
        hero_gender="girl",
        recipient_name="Ben",
    ),
    StoryParams(
        place="blanket_fort",
        solution="lamp",
        recipient="sister",
        mood="shy_day",
        hero_name="Lily",
        hero_gender="girl",
        recipient_name="Anna",
    ),
    StoryParams(
        place="hallway_bench",
        solution="move_to_bright_spot",
        recipient="friend",
        mood="shy_day",
        hero_name="Ava",
        hero_gender="girl",
        recipient_name="Zoe",
    ),
    StoryParams(
        place="attic_corner",
        solution="catch_sunbeam",
        recipient="grandpa",
        mood="tired_day",
        hero_name="Rose",
        hero_gender="girl",
        recipient_name="Grandpa Joe",
    ),
]


def explain_rejection(place: Place, solution: Solution) -> str:
    if solution.sense < SENSE_MIN:
        return (
            f"(Refusing solution '{solution.id}': it does not sensibly solve the light problem. "
            f"A kaleidoscope needs more light, not just more shaking.)"
        )
    if solution.needs_curtain and not place.has_curtain:
        return f"(No story: {place.label} has no curtain to open.)"
    if solution.needs_lamp and not place.has_lamp:
        return f"(No story: {place.label} has no lamp to turn on.)"
    if solution.needs_sunbeam and not place.has_sunbeam:
        return f"(No story: {place.label} has no sunbeam to use.)"
    if solution.needs_movable and not place.movable:
        return f"(No story: in {place.label}, they cannot simply move to a brighter spot.)"
    return (
        f"(No story: {solution.id} still would not make {place.label} bright enough for the kaleidoscope.)"
    )


ASP_RULES = r"""
works(P,S) :- place(P), solution(S), sensible(S),
              not needs_curtain(S), not needs_lamp(S), not needs_sunbeam(S), not needs_movable(S),
              base_light(P,B), gain(S,G), enough_light(E), B+G >= E.
works(P,S) :- place(P), solution(S), sensible(S),
              needs_curtain(S), has_curtain(P),
              not needs_lamp(S), not needs_sunbeam(S), not needs_movable(S),
              base_light(P,B), gain(S,G), enough_light(E), B+G >= E.
works(P,S) :- place(P), solution(S), sensible(S),
              needs_lamp(S), has_lamp(P),
              not needs_curtain(S), not needs_sunbeam(S), not needs_movable(S),
              base_light(P,B), gain(S,G), enough_light(E), B+G >= E.
works(P,S) :- place(P), solution(S), sensible(S),
              needs_sunbeam(S), has_sunbeam(P),
              not needs_curtain(S), not needs_lamp(S), not needs_movable(S),
              base_light(P,B), gain(S,G), enough_light(E), B+G >= E.
works(P,S) :- place(P), solution(S), sensible(S),
              needs_movable(S), movable(P),
              not needs_curtain(S), not needs_lamp(S), not needs_sunbeam(S),
              base_light(P,B), gain(S,G), enough_light(E), B+G >= E.

sensible(S) :- solution(S), sense(S,N), sense_min(M), N >= M.
valid(P,S) :- works(P,S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("base_light", pid, place.base_light))
        if place.has_curtain:
            lines.append(asp.fact("has_curtain", pid))
        if place.has_lamp:
            lines.append(asp.fact("has_lamp", pid))
        if place.has_sunbeam:
            lines.append(asp.fact("has_sunbeam", pid))
        if place.movable:
            lines.append(asp.fact("movable", pid))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, sol.sense))
        lines.append(asp.fact("gain", sid, sol.gain))
        if sol.needs_curtain:
            lines.append(asp.fact("needs_curtain", sid))
        if sol.needs_lamp:
            lines.append(asp.fact("needs_lamp", sid))
        if sol.needs_sunbeam:
            lines.append(asp.fact("needs_sunbeam", sid))
        if sol.needs_movable:
            lines.append(asp.fact("needs_movable", sid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("enough_light", NEEDED_LIGHT))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(s for (s,) in asp.atoms(model, "sensible"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a kaleidoscope, a dim place, a kind fix."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--recipient-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.solution:
        place = PLACES[args.place]
        solution = SOLUTIONS[args.solution]
        if not solution_works(place, solution):
            raise StoryError(explain_rejection(place, solution))
    if args.solution and SOLUTIONS[args.solution].sense < SENSE_MIN:
        raise StoryError(explain_rejection(PLACES[args.place] if args.place else next(iter(PLACES.values())), SOLUTIONS[args.solution]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.solution is None or combo[1] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, solution_id = rng.choice(sorted(combos))
    recipient_id = args.recipient or rng.choice(sorted(RECIPIENTS))
    mood_id = args.mood or rng.choice(sorted(MOODS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    recipient_name = args.recipient_name
    if recipient_name is None:
        rec = RECIPIENTS[recipient_id]
        if rec.type in {"girl"}:
            recipient_name = rng.choice(GIRL_NAMES)
        elif rec.type in {"boy"}:
            recipient_name = rng.choice(BOY_NAMES)
        elif rec.type == "grandfather":
            recipient_name = "Grandpa Joe"
        else:
            recipient_name = "Grandma May"
    return StoryParams(
        place=place_id,
        solution=solution_id,
        recipient=recipient_id,
        mood=mood_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        recipient_name=recipient_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")
    if params.recipient not in RECIPIENTS:
        raise StoryError(f"(Unknown recipient: {params.recipient})")
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")

    place = PLACES[params.place]
    solution = SOLUTIONS[params.solution]
    if not solution_works(place, solution):
        raise StoryError(explain_rejection(place, solution))

    world = tell(
        place_cfg=place,
        solution_cfg=solution,
        recipient_cfg=RECIPIENTS[params.recipient],
        mood_cfg=MOODS[params.mood],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        recipient_name=params.recipient_name,
    )

    rendered = world.render().replace("  ", " ").replace(" .", ".")
    rendered = rendered.replace(" ,", ",")
    return StorySample(
        params=params,
        story=rendered,
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
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: valid combos match ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {s.id for s in sensible_solutions()}
    if c_sens == p_sens:
        print(f"OK: sensible solutions match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible solutions: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Generated empty story.)")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show sensible/1.\n#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible solutions: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, solution) combos:\n")
        for place, solution in combos:
            print(f"  {place:14} {solution}")
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
            header = f"### {p.hero_name}: {p.place} with {p.solution} ({p.recipient})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
