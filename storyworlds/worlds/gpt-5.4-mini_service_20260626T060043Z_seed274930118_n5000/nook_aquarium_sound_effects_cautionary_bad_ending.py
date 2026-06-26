#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/nook_aquarium_sound_effects_cautionary_bad_ending.py
===============================================================================================================

A small storyworld in an aquarium nook, built from a tall-tale seed.

Premise:
- A child visits an aquarium and loves a cozy nook beside a big glass tank.
- A noisy sound-effect button promises fun, but it is not meant for sudden bangs.
- The caretaker warns the child to be gentle.

Tension:
- The child wants the biggest splashy sound in the room.
- The child ignores the warning and presses the button anyway.

Turn:
- The sound startles the fish and alarms the keeper.
- The child's favorite token slips away in the confusion.

Resolution:
- This is a cautionary tale with a bad ending: the mistake cannot be undone.
- The ending image proves the change: the nook is quiet, the child is chastened,
  and the lost token stays gone.

This script is intentionally standalone and uses only the Python stdlib plus the
shared storyworld result containers. ASP is imported lazily only when requested.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    child: object | None = None
    keeper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the aquarium"
    nook: str = "the blue-tiled nook"
    affordances: set[str] = field(default_factory=set)
    setting: object | None = None
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
class SoundEffect:
    id: str
    label: str
    verb: str
    adjective: str
    warning: str
    consequence: str
    strength: float = 1.0
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Token:
    label: str
    phrase: str
    risk: str
    type: str
    region: str = "hand"
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    current_sound: str = ""
    current_token: str = ""

    world: object | None = None
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


SOUNDS = {
    "whoosh": SoundEffect(
        id="whoosh",
        label="the whoosh button",
        verb="whoosh",
        adjective="hushy",
        warning="It makes a big whoosh, and big whooshes can scare the shy fish.",
        consequence="the water shivered and the fish shot for the weeds",
        tags={"sound", "fish", "warning"},
    ),
    "clank": SoundEffect(
        id="clank",
        label="the clank lever",
        verb="clank",
        adjective="metallic",
        warning="It makes a sharp clank, and sharp clanks can upset the glassy calm.",
        consequence="the keeper flinched and the shells rang like tiny bells",
        tags={"sound", "keeper", "warning"},
    ),
    "bellow": SoundEffect(
        id="bellow",
        label="the bellow horn",
        verb="bellow",
        adjective="thunderous",
        warning="It makes a thunderous bellow, and thunderous bellows belong far from the tanks.",
        consequence="the whole nook echoed like a barrel in a storm",
        tags={"sound", "warning", "nook"},
    ),
}

TOKENS = {
    "pearl": Token(
        label="pearl charm",
        phrase="a tiny pearl charm on a string",
        risk="it could slip into the drain grating",
        type="charm",
        plural=False,
    ),
    "shell": Token(
        label="shell whistle",
        phrase="a little shell whistle",
        risk="it could rattle loose and get lost in the rush",
        type="whistle",
        plural=False,
    ),
    "badge": Token(
        label="badge lanyard",
        phrase="a bright visitor badge on a cord",
        risk="it could fly off in a scramble",
        type="badge",
        plural=False,
    ),
}

NAMES = ["Mina", "Theo", "Ruby", "Finn", "Lena", "Pip", "Milo", "Nora"]
TRAITS = ["bold", "curious", "spunky", "tall-tale-minded", "restless"]


class AquariumWorld(World):
    pass


def sound_at_risk(sound: SoundEffect, token: Token) -> bool:
    return True  # in this tale, every sound is tempting but dangerous


def choose_sound(rng: random.Random) -> SoundEffect:
    return _safe_lookup(SOUNDS, rng.choice(sorted(SOUNDS)))


def choose_token(rng: random.Random) -> Token:
    return _safe_lookup(TOKENS, rng.choice(sorted(TOKENS)))


def valid_combos() -> list[tuple[str, str, str]]:
    return [("aquarium", sid, tid) for sid in SOUNDS for tid in TOKENS]


def explain_rejection(sound: SoundEffect, token: Token) -> str:
    return (
        f"(No story: the cautionary bad ending needs a sound effect that can cause "
        f"a real scramble, and {sound.label} with {token.label} does that here.)"
    )


@dataclass
class StoryParams:
    setting: str
    sound: str
    token: str
    name: str
    trait: str
    caretaker: str
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


def build_world(params: StoryParams) -> World:
    setting = Setting()
    world = AquariumWorld(setting=setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="boy" if params.name in {"Theo", "Finn", "Milo", "Pip"} else "girl",
        meters={"walk": 1.0},
        memes={"want": 0.0, "warning": 0.0, "regret": 0.0},
    ))
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type=params.caretaker,
        label="the keeper",
        meters={"work": 1.0},
        memes={"care": 1.0},
    ))
    sound = _safe_lookup(SOUNDS, params.sound)
    token = _safe_lookup(TOKENS, params.token)
    charm = world.add(Entity(
        id="token",
        type=token.type,
        label=token.label,
        phrase=token.phrase,
        owner=child.id,
        caretaker=keeper.id,
        meters={"safe": 1.0},
    ))

    world.current_sound = sound.id
    world.current_token = token.id

    # Act 1
    world.say(
        f"In the aquarium stood a little nook with blue tiles and a glass wall that "
        f"looked into the deep green water."
    )
    world.say(
        f"There lived {child.id}, a {params.trait} child who loved anything that sounded "
        f"grand enough to make the jellyfish blink."
    )
    world.say(
        f"{child.id} wore {charm.phrase}, and {child.pronoun('possessive')} favorite game was "
        f"to stand in the nook and listen for the biggest echo."
    )

    # Act 2
    world.para()
    world.say(
        f"One afternoon {child.id} discovered {sound.label} beside the tank."
    )
    world.say(
        f"{sound.warning}"
    )
    child.memes["warning"] += 1.0
    child.memes["want"] += 1.0
    world.say(
        f"{keeper.pronoun().capitalize()} put up a hand and said, "
        f"\"Don't press it in the nook. The fish are little, and little fish have little nerves.\""
    )
    world.say(
        f"But {child.id} wanted to hear {sound.verb} anyway."
    )
    world.say(
        f"{child.id} pressed the button with two quick fingers."
    )
    child.meters["press"] = child.meters.get("press", 0.0) + 1.0

    # Consequence
    world.para()
    world.say(
        f"{sound.consequence}."
    )
    child.meters["noise"] = child.meters.get("noise", 0.0) + sound.strength
    child.memes["regret"] += 1.0
    keeper.meters["work"] += 1.0

    if token.label == "badge lanyard":
        world.say(
            f"In the scramble, {child.id}'s badge lanyard slipped from {child.pronoun('possessive')} "
            f"neck and skated beneath the bench."
        )
    elif token.label == "shell whistle":
        world.say(
            f"In the scramble, {child.id}'s shell whistle bounced once, twice, and vanished behind a fern pot."
        )
    else:
        world.say(
            f"In the scramble, {child.id}'s pearl charm slid away and flashed once in the drain grate."
        )
    charm.meters["lost"] = 1.0
    charm.meters["safe"] = 0.0
    child.meters["lost"] = 1.0

    # Bad ending
    world.para()
    world.say(
        f"{keeper.pronoun().capitalize()} had to close the nook early and guide {child.id} away from the glass."
    )
    world.say(
        f"The shy fish stayed hidden, the nook stayed quiet, and {child.id} had to go home without {charm.label}."
    )
    world.say(
        f"That was the lesson: a big sound can leave a small heart heavy."
    )
    child.memes["regret"] += 1.0
    world.facts = {
        "child": child,
        "keeper": keeper,
        "sound": sound,
        "token": token,
        "charm": charm,
        "setting": setting,
        "bad_ending": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    sound = _safe_fact(world, f, "sound")
    token = _safe_fact(world, f, "token")
    return [
        f'Write a tall-tale style cautionary story set in an aquarium nook that includes "{sound.verb}" and ends badly.',
        f"Tell a short story about {child.id} in the aquarium who ignores a warning about {sound.label} and loses {token.label}.",
        f'Create a child-facing story where a child in a nook hears a sound effect, should stop, but does not.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    keeper = _safe_fact(world, f, "keeper")
    sound = _safe_fact(world, f, "sound")
    token = _safe_fact(world, f, "token")
    return [
        QAItem(
            question=f"Where was {child.id} when the trouble started?",
            answer="The trouble started in the aquarium, in a little nook beside the glass tank.",
        ),
        QAItem(
            question=f"What warning did {keeper.label} give about {sound.label}?",
            answer=sound.warning,
        ),
        QAItem(
            question=f"What happened after {child.id} pressed the button?",
            answer=(
                f"{sound.consequence}, and {child.id}'s {token.label} got lost in the scramble."
            ),
        ),
        QAItem(
            question=f"Did the story end happily?",
            answer="No. This was a cautionary story with a bad ending, so the mistake stayed costly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aquarium?",
            answer="An aquarium is a place where people can look at fish and other water animals through glass tanks.",
        ),
        QAItem(
            question="What is a nook?",
            answer="A nook is a small cozy corner or little space tucked away from the rest of a room.",
        ),
        QAItem(
            question="Why can loud sounds bother fish?",
            answer="Loud sounds can startle fish because water carries vibrations very well, so a big noise can feel sudden and scary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
sound_risky(S) :- sound(S).
cautionary(S,T) :- sound(S), token(T).
bad_ending(S,T) :- sound_risky(S), cautionary(S,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    for tid in TOKENS:
        lines.append(asp.fact("token", tid))
    lines.append(asp.fact("setting", "aquarium"))
    lines.append(asp.fact("nook", "aquarium_nook"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/2."))
    return sorted(set(asp.atoms(model, "bad_ending")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set((s, t) for s in SOUNDS for t in TOKENS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Aquarium nook sound-effect cautionary storyworld.")
    ap.add_argument("--place", choices=["aquarium"], default="aquarium")
    ap.add_argument("--sound", choices=sorted(SOUNDS))
    ap.add_argument("--token", choices=sorted(TOKENS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--caretaker", choices=["mother", "father"], default="mother")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    sound = getattr(args, "sound", None) or rng.choice(sorted(SOUNDS))
    token = getattr(args, "token", None) or rng.choice(sorted(TOKENS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    caretaker = getattr(args, "caretaker", None) or rng.choice(["mother", "father"])
    return StoryParams(
        setting="aquarium",
        sound=sound,
        token=token,
        name=name,
        trait=trait,
        caretaker=caretaker,
    )


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


CURATED = [
    StoryParams(setting="aquarium", sound="whoosh", token="pearl", name="Mina", trait="curious", caretaker="mother"),
    StoryParams(setting="aquarium", sound="clank", token="shell", name="Theo", trait="restless", caretaker="father"),
    StoryParams(setting="aquarium", sound="bellow", token="badge", name="Ruby", trait="bold", caretaker="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_ending/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show bad_ending/2."))
        combos = sorted(set(asp.atoms(model, "bad_ending")))
        for s, t in combos:
            print(f"{s} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
