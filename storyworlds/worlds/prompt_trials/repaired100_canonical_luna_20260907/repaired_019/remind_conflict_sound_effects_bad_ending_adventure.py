#!/usr/bin/env python3
"""
A standalone storyworld about a reminder, a noisy adventure, and a bad ending.

Luna must cross a windy ravine to return a lost bell. Her friend reminds her
to check the bridge ropes before stepping out. Luna hears warning sounds, but
conflict and impatience make her ignore the reminder. The bridge gives way,
and the adventure ends badly with the bell lost below.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Character:
    name: str
    kind: str
    trait: str
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    friend: object | None = None
    hero: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Ravine:
    name: str
    weather: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    ravine: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class AdventureArc:
    object_name: str
    object_description: str
    goal: str
    warning_sound: str
    sound_comparison: str
    bridge_problem: str
    conflict_line: str
    reminder: str
    bad_turn: str
    consequence: str
    ending_image: str
    helper_action: str
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    name: str = ""
    kind: str = ""
    trait: str = ""
    weather: str = ""
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


KINDS = ["rabbit", "fox", "mouse", "badger", "squirrel"]
TRAITS = ["curious", "brave", "hopeful", "restless", "kind"]
WEATHERS = {
    "windy": "a hard silver wind",
    "misty": "a cold gray mist",
    "rainy": "a sudden spring rain",
    "sunny": "bright morning sun",
}
NAMES = {
    "rabbit": ["Luna", "Pip", "Tansy"],
    "fox": ["Luna", "Rook", "Mira"],
    "mouse": ["Luna", "Nim", "Clover"],
    "badger": ["Luna", "Bram", "Moss"],
    "squirrel": ["Luna", "Fenn", "Perri"],
}

ARCS = [
    AdventureArc(
        object_name="silver bell",
        object_description="a little silver bell from the mountain shrine",
        goal="return the bell before the evening ceremony",
        warning_sound="creak-creak",
        sound_comparison="an old door trying to whisper",
        bridge_problem="the left rope had frayed nearly through",
        conflict_line="You always tell me to wait",
        reminder="test every bridge rope before crossing",
        bad_turn="the frayed rope snapped beneath Luna's foot",
        consequence="the bell flew from her paws into the dark stream",
        ending_image="the empty bell strap hung from a broken plank while the stream carried the bell away",
        helper_action="threw a vine around Luna's waist and pulled her back to the bank",
    ),
    AdventureArc(
        object_name="red map case",
        object_description="a red map case holding the trail map",
        goal="bring the map to the lost hikers beyond the ravine",
        warning_sound="clack-clack",
        sound_comparison="two stones knocking teeth",
        bridge_problem="three wooden pegs had loosened in the middle span",
        conflict_line="I know this path better than you",
        reminder="look for loose pegs before trusting a bridge",
        bad_turn="a loose peg popped free as Luna hurried across",
        consequence="the map case spun into the mist below",
        ending_image="blank map strings fluttered from the bank as the trail disappeared in fog",
        helper_action="caught Luna's sleeve with a long branch",
    ),
    AdventureArc(
        object_name="blue lantern",
        object_description="a blue lantern meant for the cave entrance",
        goal="carry the lantern to the explorers waiting in the cave",
        warning_sound="tink-tink",
        sound_comparison="a spoon trembling in a cup",
        bridge_problem="the bridge boards were slick with rain",
        conflict_line="If I stop now, everyone will call me afraid",
        reminder="wipe wet boards and cross one careful step at a time",
        bad_turn="Luna's foot slid from a rain-slick board",
        consequence="the lantern struck a stone and its flame went out below",
        ending_image="the dark cave mouth waited while the broken lantern bobbed in the flood",
        helper_action="pulled Luna toward a dry root above the bank",
    ),
    AdventureArc(
        object_name="golden feather",
        object_description="a golden feather promised to the queen eagle",
        goal="climb across the ravine and deliver the feather before sunset",
        warning_sound="whump-whump",
        sound_comparison="a tired drum under a blanket",
        bridge_problem="the hanging bridge swung wildly in the crosswind",
        conflict_line="I cannot turn back after coming this far",
        reminder="tie down the bridge before taking the first step",
        bad_turn="a gust twisted the untied bridge sideways",
        consequence="the feather escaped and vanished over the cliff",
        ending_image="the queen eagle circled above an empty paw while the bridge knocked against the rocks",
        helper_action="grabbed Luna's backpack and dragged her onto the ledge",
    ),
]

OPENINGS = [
    "Luna loved a path that curled beyond the next hill.",
    "At dawn, Luna found an adventure waiting beside the old ravine.",
    "The mountain trail glittered, and Luna thought it was calling her name.",
    "Luna had packed quickly because important journeys never seemed to wait.",
]

DIALOGUE = [
    '"Luna, remember: ' + "{reminder}" + '," called her friend Rowan.',
    '"Please remind me if I rush," Luna said, though her paws were already moving.',
    '"The bridge is making a warning sound," Rowan said. "We should listen."',
    '"I heard it," Luna answered. "But the adventure cannot wait."',
]

LESSONS = [
    "A reminder is useful only when someone chooses to remember it.",
    "Bravery without attention can turn a good adventure into a dangerous one.",
    "A warning sound is a message, not a challenge.",
    "When a friend reminds you to be careful, stopping is part of going on.",
]


class World:
    def __init__(self, ravine: Ravine) -> None:
        self.ravine = ravine
        self.hero: Optional[Character] = None
        self.friend: Optional[Character] = None
        self.arc: Optional[AdventureArc] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.ravine.meters = {"bridge_strength": 1.0, "danger": 0.0}
        self.ravine.memes = {"trust": 0.0, "regret": 0.0}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def build_world(params: StoryParams) -> World:
    key = f"{params.name}|{params.kind}|{params.trait}|{params.weather}|{params.seed}"
    choice = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c) for i, c in enumerate(key)
    )
    ravine = Ravine(name="Whispering Ravine", weather=_safe_lookup(WEATHERS, params.weather))
    world = World(ravine)
    world.hero = Character(params.name, params.kind, params.trait)
    world.friend = Character("Rowan", "raven", "careful")
    world.arc = _safe_lookup(ARCS, choice % len(ARCS))
    world.facts["opening"] = _safe_lookup(OPENINGS, (choice // len(ARCS)) % len(OPENINGS))
    world.facts["lesson"] = _safe_lookup(LESSONS, (choice * 3) % len(LESSONS))
    world.facts["dialogue_one"] = DIALOGUE[(choice * 5) % len(DIALOGUE)].format(
        reminder=world.arc.reminder
    )
    return world


def remind(world: World) -> None:
    if "remind" in world.fired:
        return
    world.fired.add("remind")
    world.hero.memes["remembered"] = 1.0
    world.say(
        f'Rowan called after her, "Luna, remember: {world.arc.reminder}." '
        f"Luna heard the reminder, but the wind tugged at her scarf."
    )


def begin_conflict(world: World) -> None:
    if "conflict" in world.fired:
        return
    world.fired.add("conflict")
    world.hero.memes["impatience"] = 1.0
    world.say(
        f'"{world.arc.conflict_line}," Luna replied. '
        f'"I promised to {world.arc.goal}, and I will not be late."'
    )


def hear_warning(world: World) -> None:
    if "warning" in world.fired:
        return
    world.fired.add("warning")
    world.ravine.meters["danger"] = 1.0
    world.ravine.meters["bridge_strength"] = 0.45
    world.say(
        f"The bridge answered with {world.arc.warning_sound}, "
        f"like {world.arc.sound_comparison}. Rowan pointed out that {world.arc.bridge_problem}."
    )


def cross_badly(world: World) -> None:
    if "cross" in world.fired:
        return
    world.fired.add("cross")
    if "warning" not in world.fired:
        pass
    world.hero.memes["ignored_reminder"] = 1.0
    world.ravine.meters["bridge_strength"] = 0.0
    world.ravine.memes["regret"] = 1.0
    world.say(
        f"Luna stepped onto the bridge anyway. {world.arc.bad_turn.capitalize()}. "
        f"She reached for the {world.arc.object_name}, but {world.arc.consequence}."
    )


def rescue_and_conclude(world: World) -> None:
    if "conclude" in world.fired:
        return
    world.fired.add("conclude")
    world.say(
        f"Rowan {world.arc.helper_action}. Luna reached the bank, shaken and muddy, "
        f"but the mission had failed. {world.arc.ending_image.capitalize()}."
    )
    world.say(
        f"Luna looked at Rowan and whispered, 'Next time I will remember before I move.' "
        f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "lesson")}"
    )


def tell_story(world: World) -> None:
    hero = world.hero
    arc = world.arc
    world.say(f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "opening")} Her name was {hero.name}, a {hero.trait} little {hero.kind}.")
    world.say(
        f"That morning, {hero.name} carried {arc.object_description} toward {world.ravine.name} "
        f"because she meant to {arc.goal}."
    )
    world.para()
    world.say(
        f"At the ravine, {world.ravine.weather} pushed against the hanging bridge. "
        f"{hero.name} saw the far trail and hurried toward it."
    )
    remind(world)
    begin_conflict(world)
    hear_warning(world)
    world.say(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "dialogue_one"))
    cross_badly(world)
    world.para()
    rescue_and_conclude(world)
    world.facts.update(
        resolved=False,
        failed=True,
        object_name=arc.object_name,
        goal=arc.goal,
        warning=arc.warning_sound,
        bridge_problem=arc.bridge_problem,
        consequence=arc.consequence,
        lesson=_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "lesson"),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write an adventure about {world.hero.name} crossing {world.ravine.name} with a {world.arc.object_name}.",
        f"Include a reminder to {world.arc.reminder}, conflict, and the sound {world.arc.warning_sound}.",
        f"End badly when the warning is ignored and {world.arc.consequence}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What did Rowan remind {world.hero.name} to do?",
            answer=f"Rowan reminded {world.hero.name} to {world.arc.reminder} before crossing the bridge.",
        ),
        QAItem(
            question=f"What warning sound did the bridge make?",
            answer=f"The bridge made {world.arc.warning_sound}, like {world.arc.sound_comparison}.",
        ),
        QAItem(
            question=f"What conflict did {world.hero.name} face?",
            answer=(
                f"{world.hero.name} wanted to finish the adventure quickly, while Rowan urged careful action "
                f"because {world.arc.bridge_problem}."
            ),
        ),
        QAItem(
            question=f"Why did the adventure end badly?",
            answer=(
                f"{world.hero.name} ignored the reminder and crossed despite the warning. "
                f"{world.arc.bad_turn.capitalize()}, and {world.arc.consequence}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reminder?",
            answer="A reminder is a message that helps someone remember something important.",
        ),
        QAItem(
            question="Why can sound effects matter in an adventure?",
            answer="Sound effects can warn characters that a place, object, or action may be dangerous.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is a problem or disagreement that makes a character choose what to do.",
        ),
        QAItem(
            question="What makes an ending bad?",
            answer="A bad ending shows that the main problem was not solved or that ignoring a warning caused a serious loss.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"ravine={world.ravine.name}",
            f"weather={world.ravine.weather}",
            f"hero={world.hero.name} ({world.hero.kind}, {world.hero.trait})",
            f"object={world.arc.object_name}",
            f"warning={world.arc.warning_sound}",
            f"bridge_problem={world.arc.bridge_problem}",
            f"failed={world.facts.get('failed')}",
            f"meters={world.ravine.meters}",
            f"memes={world.ravine.memes}",
            f"fired={sorted(world.fired)}",
        ]
    )


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (kind, trait, weather)
        for kind in KINDS
        for trait in TRAITS
        for weather in WEATHERS
    ]


ASP_RULES = r"""
kind(K) :- kind_name(K).
trait(T) :- trait_name(T).
weather(W) :- weather_name(W).
valid(K,T,W) :- kind(K), trait(T), weather(W).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for value in KINDS:
        lines.append(asp.fact("kind_name", value))
    for value in TRAITS:
        lines.append(asp.fact("trait_name", value))
    for value in WEATHERS:
        lines.append(asp.fact("weather_name", value))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP registries.")
        return 1
    print(f"OK: ASP/Python parity holds for {len(py)} combinations.")
    for params in CURATED:
        sample = generate(params)
        if not sample.story or sample.world is None:
            print("MISMATCH: generated sample is incomplete.")
            return 1
    print(f"OK: exercised {len(CURATED)} generated stories.")
    return 0


@dataclass
class _Args:
    kind: Optional[str] = None
    trait: Optional[str] = None
    weather: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


CURATED = [
    StoryParams("Luna", "rabbit", "curious", "windy"),
    StoryParams("Luna", "fox", "brave", "misty"),
    StoryParams("Luna", "mouse", "hopeful", "rainy"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an adventure about Luna, a reminder, and a dangerous bridge."
    )
    parser.add_argument("--kind", choices=KINDS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--weather", choices=list(WEATHERS))
    parser.add_argument("--name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kind = getattr(args, "kind", None) or rng.choice(KINDS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    weather = getattr(args, "weather", None) or rng.choice(list(WEATHERS))
    name = getattr(args, "name", None) or ("Luna" if rng.random() < 0.75 else rng.choice(_safe_lookup(NAMES, kind)))
    return StoryParams(name, kind, trait, weather)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:\n")
        for kind, trait, weather in combos:
            print(f"  {kind:10} {trait:10} {weather}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(max(0, getattr(args, "n", None))):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        params = sample.params
        header = ""
        if getattr(args, "all", None):
            header = f"### {params.name}: {params.kind}, {params.weather} adventure"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
