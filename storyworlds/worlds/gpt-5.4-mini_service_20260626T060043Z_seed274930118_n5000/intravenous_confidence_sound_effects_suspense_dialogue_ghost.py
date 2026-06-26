#!/usr/bin/env python3
"""
storyworlds/worlds/intravenous_confidence_sound_effects_suspense_dialogue_ghost.py
===================================================================================

A small ghost-story world built around a nighttime hospital room, a humming
intravenous drip, nervous confidence, sound effects, suspense, and dialogue.

Seed tale:
---
A child lies in a quiet hospital room with an intravenous line in one arm.
At night, the room fills with little sounds: drip... drip... drip. The child
thinks those sounds mean a ghost is near. A pale shape appears in the doorway
and the child freezes. Then the shape whispers, and the child finds enough
confidence to answer back. The ghost is not mean at all. It is only lonely,
and it leads the child to a kind answer and a calmer night.

World model:
---
* physical meters: noise, light, distance, worry, comfort, stillness
* emotional memes: fear, confidence, curiosity, kindness, loneliness, relief

Story shape:
---
setup -> suspense -> dialogue -> reveal -> resolution

The world is designed to read like a complete child-facing ghost story while
remaining driven by simulated state.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "nurse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Setting:
    place: str
    time: str
    affordances: set[str] = field(default_factory=set)
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
class Sound:
    id: str
    onomatopoeia: str
    source: str
    mood: str
    kind: str
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


@dataclass
class StoryParams:
    place: str
    sound: str
    hero: str
    hero_type: str
    helper: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.sound_sequence: list[str] = []
        self.trace: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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

    def log(self, message: str) -> None:
        self.trace.append(message)


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hospital_room": Setting(
        place="the quiet hospital room",
        time="night",
        affordances={"listen", "whisper", "comfort"},
    ),
    "hallway": Setting(
        place="the dim hallway",
        time="night",
        affordances={"listen", "whisper", "comfort"},
    ),
}

SOUNDS = {
    "iv_drip": Sound(
        id="iv_drip",
        onomatopoeia="drip... drip... drip...",
        source="the intravenous bottle",
        mood="spooky",
        kind="drip",
    ),
    "window_tap": Sound(
        id="window_tap",
        onomatopoeia="tap... tap... tap...",
        source="the window",
        mood="spooky",
        kind="tap",
    ),
    "soft_whisper": Sound(
        id="soft_whisper",
        onomatopoeia="hush...",
        source="the ghost",
        mood="gentle",
        kind="whisper",
    ),
}

HERO_NAMES = ["Milo", "Nina", "Leo", "Ivy", "June", "Owen", "Maya", "Noah"]
HELPER_NAMES = ["Nurse Bea", "Nurse Sol", "Aunt Dot", "Dad", "Mom"]

TRAITS = ["small", "brave", "sleepy", "curious", "shy", "careful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when it has a quiet night setting and a spooky sound.
valid_story(P, S, H) :- place(P), sound(S), hero(H),
    allows(P, listen), spooky(S).

% Confidence can calm fear only after dialogue and a reveal.
resolved(P, S, H) :- valid_story(P, S, H), has_dialogue(H), reveal(S), confidence(H).

% A ghost-story candidate must include intravenous context.
ghost_story(P, S) :- valid_story(P, S, _), intravenous_context(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("allows", pid, "listen"))
        lines.append(asp.fact("allows", pid, "whisper"))
        lines.append(asp.fact("allows", pid, "comfort"))
        if "hospital" in setting.place:
            lines.append(asp.fact("intravenous_context", pid))
    for sid, snd in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if snd.mood == "spooky":
            lines.append(asp.fact("spooky", sid))
    for name in HERO_NAMES:
        lines.append(asp.fact("hero", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n#show resolved/3.\n"))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    py = set((p, s, h) for (p, s, h) in valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "listen" not in setting.affordances:
            continue
        for sound in SOUNDS:
            for hero in HERO_NAMES:
                combos.append((place, sound, hero))
    return combos


def explain_rejection(place: str, sound: str) -> str:
    return (
        f"(No story: {sound} does not fit the quiet ghost-story setup at {place}. "
        f"Choose a sound that can plausibly make a child think a ghost is near.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def is_spooky_sound(sound: Sound) -> bool:
    return sound.mood == "spooky"


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    trait = next((t for t in hero.traits if t != "small"), "small")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} in {world.setting.place} at night, "
        f"with an intravenous line resting carefully in {hero.pronoun('possessive')} arm."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had {helper.label} nearby, but the room still felt big and hush-hush."
    )


def add_sound(world: World, sound: Sound) -> None:
    world.sound_sequence.append(sound.onomatopoeia)
    if sound.id == "iv_drip":
        world.say(
            f"Then the room began to say it softly: {sound.onomatopoeia} The sound came from {sound.source}, "
            f"and it seemed to fill the dark corners."
        )
    else:
        world.say(
            f"Outside or close by, something answered: {sound.onomatopoeia} It made {world.get('hero').id} stare at the door."
        )
    world.facts["sound_source"] = sound.source
    world.facts["sound_kind"] = sound.kind


def suspense(world: World, hero: Entity, sound: Sound) -> None:
    hero.memes["fear"] += 1.0
    hero.meters["worry"] += 1.0
    hero.meters["stillness"] += 1.0
    world.say(
        f"{hero.id} held very still and listened. Every little noise felt bigger in the dark."
    )
    if is_spooky_sound(sound):
        world.say(
            f"{hero.id} wondered if the dripping and tapping were footsteps from a ghost."
        )
    else:
        world.say(
            f"{hero.id} wondered why the quiet would suddenly move."
        )
    world.log("suspense: fear and worry rose")


def reveal_ghost(world: World) -> Entity:
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            label="the ghost",
            traits=["pale", "lonely"],
            meters={"distance": 3.0, "light": 0.2},
            memes={"loneliness": 1.0, "curiosity": 1.0},
        )
    )
    world.say(
        "At the doorway, a pale shape wavered like mist in a lamp glow."
    )
    world.say(
        "It did not rush. It only hovered and let the silence stretch."
    )
    world.log("ghost appears")
    return ghost


def dialogue(world: World, hero: Entity, ghost: Entity, helper: Entity, sound: Sound) -> None:
    hero.memes["confidence"] += 1.0
    world.facts["has_dialogue"] = True
    world.say(
        f'"Who are you?" {hero.id} whispered, even though {hero.pronoun("possessive")} voice shook a little.'
    )
    world.say(
        f'"I am only a lonely ghost," said the shape. "I heard {sound.onomatopoeia} and thought someone was awake."'
    )
    world.say(
        f'{helper.label} stepped closer and said, "You do not have to be scared. That sound is the '
        f'intravenous drip doing its work, and it means the medicine is going where it should."'
    )
    world.say(
        f'{hero.id} blinked. "So it is not a secret ghost trick?"'
    )
    world.say(
        f'"No," said {helper.label}, smiling. "Just a tiny nightly sound."'
    )
    world.say(
        f'The ghost tilted its head and added, "I only make the room feel spooky because I forget how much sound an empty hall can hold."'
    )
    world.log("dialogue: fear met explanation")


def turn_and_resolution(world: World, hero: Entity, ghost: Entity, helper: Entity) -> None:
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["confidence"] += 1.0
    hero.memes["kindness"] += 1.0
    ghost.memes["loneliness"] = max(0.0, ghost.memes["loneliness"] - 1.0)
    ghost.memes["relief"] = ghost.memes.get("relief", 0.0) + 1.0
    hero.meters["worry"] = max(0.0, hero.meters["worry"] - 1.0)
    hero.meters["comfort"] += 1.0
    world.facts["reveal"] = True
    world.say(
        f'{hero.id} took a deeper breath and found {hero.pronoun("possessive")} confidence growing warm in {hero.pronoun("possessive")} chest.'
    )
    world.say(
        f'"You can stay," {hero.id} told the ghost. "The room is not as scary now."'
    )
    world.say(
        f"The ghost smiled into a thin moonbeam, and the room felt less wide and more like a nest."
    )
    world.say(
        f"{helper.label} pulled the blanket up, and the drip still went {world.sound_sequence[0]} in the background, but now it sounded like a clock keeping watch."
    )
    world.say(
        f"By the end, {hero.id} lay calm and awake, the ghost was no longer lonely, and the night stayed quiet except for the gentle intravenous rhythm."
    )
    world.log("resolution: confidence and kindness settle the room")


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=params.hero_type,
            label=params.hero,
            traits=["small", random.choice(TRAITS), "brave"],
            meters={"worry": 0.0, "comfort": 0.0},
            memes={"fear": 0.0, "confidence": 0.0, "kindness": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="nurse" if params.helper.startswith("Nurse") else "adult",
            label=params.helper,
            meters={"light": 1.0},
            memes={"calm": 1.0},
        )
    )
    sound = _safe_lookup(SOUNDS, params.sound)
    world.facts.update(
        hero=hero,
        helper=helper,
        sound=sound,
        place=params.place,
        intravenous=True,
    )
    introduce(world, hero, helper)
    world.para()
    add_sound(world, sound)
    suspense(world, hero, sound)
    world.para()
    ghost = reveal_ghost(world)
    dialogue(world, hero, ghost, helper, sound)
    world.para()
    turn_and_resolution(world, hero, ghost, helper)
    world.facts["ghost"] = ghost
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    sound: Sound = _safe_fact(world, f, "sound")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    return [
        f'Write a gentle ghost story for a young child that includes "{sound.onomatopoeia}" and the word "intravenous".',
        f"Tell a suspenseful but kind story where {hero.label} hears {sound.onomatopoeia} at night and grows more confident with help from {helper.label}.",
        f'Write a bedside ghost story with sound effects, dialogue, and a happy ending about confidence.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    sound: Sound = _safe_fact(world, world.facts, "sound")  # type: ignore[assignment]
    ghost: Entity = _safe_fact(world, world.facts, "ghost")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {hero.label} think a ghost might be nearby?",
            answer=(
                f"{hero.label} heard {sound.onomatopoeia} in the quiet night room and the sound felt spooky, "
                f"especially with the intravenous drip making the darkness seem busy."
            ),
        ),
        QAItem(
            question=f"What helped {hero.label} feel more confident?",
            answer=(
                f"{helper.label} explained that the sound was only the intravenous drip doing its work, "
                f"and then the ghost spoke kindly instead of frightening anyone."
            ),
        ),
        QAItem(
            question="What did the ghost want?",
            answer=(
                f"The ghost was lonely and wanted someone to notice it. Once {hero.label} answered back, "
                f"the ghost felt less lonely and the room felt calmer."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "intravenous": [
        QAItem(
            question="What is an intravenous line for?",
            answer=(
                "An intravenous line, often called an IV, helps medicine or fluids go straight into the body "
                "through a tiny tube."
            ),
        )
    ],
    "confidence": [
        QAItem(
            question="What does confidence mean?",
            answer=(
                "Confidence means feeling sure enough to speak, try, or keep going even when something seems scary."
            ),
        )
    ],
    "sound": [
        QAItem(
            question="What is a sound effect in a story?",
            answer=(
                "A sound effect is a word like drip or tap that helps the reader hear what is happening in the scene."
            ),
        )
    ],
    "ghost": [
        QAItem(
            question="What is a ghost in a story?",
            answer=(
                "A ghost in a story is usually a spooky-looking spirit or shape that may startle people, but it can also be lonely or kind."
            ),
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["intravenous"],
        *WORLD_KNOWLEDGE["confidence"],
        *WORLD_KNOWLEDGE["sound"],
        *WORLD_KNOWLEDGE["ghost"],
    ]


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  sounds: {world.sound_sequence}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    lines.append(f"  trace: {world.trace}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    sound: str
    hero: str
    hero_type: str
    helper: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with intravenous suspense and confidence.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--sound", choices=SOUNDS.keys())
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    sound = getattr(args, "sound", None) or rng.choice(list(SOUNDS.keys()))
    if getattr(args, "place", None) and getattr(args, "sound", None):
        if (place, sound, _safe_lookup(HERO_NAMES, 0)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, sound=sound, hero=hero, hero_type=hero_type, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n"))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="hospital_room", sound="iv_drip", hero="Milo", hero_type="boy", helper="Nurse Bea"),
    StoryParams(place="hospital_room", sound="window_tap", hero="Ivy", hero_type="girl", helper="Mom"),
    StoryParams(place="hallway", sound="iv_drip", hero="June", hero_type="girl", helper="Nurse Sol"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3.\n#show resolved/3.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story triples:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
