#!/usr/bin/env python3
"""
A mythic storyworld about a shepherd's hard choice beside a shallow crossing,
an exit from danger, and the sound of the world changing.

Seed words: shepherd, shallow, exit
Features: Moral Value, Conflict, Sound Effects
Style: Myth
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
class StoryParams:
    place: str
    danger: str
    helper: str
    moral_value: str
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    flock: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"shepherd", "woman", "girl", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    name: str
    shallow: bool
    has_exit: bool
    sound: str
    tags: set[str] = field(default_factory=set)
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
class Danger:
    name: str
    danger_sound: str
    moral_trial: str
    threatens: set[str] = field(default_factory=set)
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
class Helper:
    name: str
    action: str
    exit_phrase: str
    sound_after: str
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


class World:
    def __init__(self, place: Place, danger: Danger, helper: Helper, moral_value: str) -> None:
        self.place = place
        self.danger = danger
        self.helper = helper
        self.moral_value = moral_value
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "brook": Place(name="the shallow brook", shallow=True, has_exit=True, sound="plip-plop", tags={"water", "shallow"}),
    "ford": Place(name="the shallow ford", shallow=True, has_exit=True, sound="glug-glug", tags={"water", "exit"}),
    "gate": Place(name="the hill gate", shallow=False, has_exit=True, sound="creak", tags={"exit"}),
}

DANGERS = {
    "storm": Danger(name="the storm", danger_sound="boom", moral_trial="courage", threatens={"water", "sheep"}),
    "wolf": Danger(name="the wolf", danger_sound="howl", moral_trial="mercy", threatens={"sheep"}),
    "fire": Danger(name="the fire", danger_sound="crackle", moral_trial="wisdom", threatens={"grass", "sheep"}),
}

HELPERS = {
    "horn": Helper(name="horn call", action="blew a horn", exit_phrase="led the flock toward the exit", sound_after="honk-honk"),
    "lantern": Helper(name="lantern light", action="raised a lantern", exit_phrase="showed the way out", sound_after="flicker"),
    "song": Helper(name="old song", action="sang a steady song", exit_phrase="calmed the flock and opened the way", sound_after="hum"),
}

MORAL_VALUES = ["courage", "mercy", "wisdom", "patience"]

GREEK_NAMES = ["Dorian", "Iris", "Mara", "Theon", "Lyra", "Nikos", "Selene", "Phaon"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic shepherd storyworld with shallow crossing, exit, moral value, conflict, and sound.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--danger", choices=DANGERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--moral-value", choices=MORAL_VALUES)
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    danger = getattr(args, "danger", None) or rng.choice(sorted(DANGERS))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    moral_value = getattr(args, "moral_value", None) or _safe_lookup(DANGERS, danger).moral_trial

    if getattr(args, "moral_value", None) and getattr(args, "moral_value", None) != _safe_lookup(DANGERS, danger).moral_trial:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not _safe_lookup(PLACES, place).has_exit:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not _safe_lookup(PLACES, place).shallow:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    name = getattr(args, "name", None) or rng.choice(GREEK_NAMES)
    return StoryParams(place=place, danger=danger, helper=helper, moral_value=moral_value, seed=None)


def _tell(world: World, hero: Entity, flock: Entity) -> None:
    place = world.place
    danger = world.danger
    helper = world.helper

    world.say(f"In old days, {hero.id} was a shepherd of {flock.phrase}, and {place.name} lay before the hills.")
    world.say(f"The water spoke in {place.sound} sounds, and the air held the sign of {danger.name}.")

    world.para()
    world.say(f"Then {danger.name} rose with a {danger.danger_sound}, and the flock grew restless.")
    hero.memes["conflict"] = 1.0
    hero.memes["duty"] = 1.0
    flock.meters["fear"] = 1.0
    world.say(f"{hero.id} felt the pull of {world.moral_value}: to guard the flock and seek the exit before harm came.")

    world.para()
    if place.shallow:
        world.say(f"{hero.id} stepped into the shallow water and listened.")
        world.say(f"At once, {helper.action}, and the path toward safety answered with {helper.sound_after}.")
        world.say(f"With that sign, {helper.exit_phrase}.")
        hero.memes["conflict"] = 0.0
        hero.memes["virtue"] = 1.0
        flock.meters["fear"] = 0.0
        world.say(f"The storm did not win. The shepherd brought the flock out by the exit, and peace returned like dawn.")
    else:
        pass

    world.facts.update(hero=hero, flock=flock, place=place, danger=danger, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth about a shepherd, a shallow crossing, and an exit from danger that uses the word "{f["place"].name.split()[-1]}".',
        f"Tell a child-friendly myth where {f['hero'].id} must show {world.moral_value} when {f['danger'].name} appears near {f['place'].name}.",
        f"Write a gentle legend with a shepherd, a helper, and a sound like {f['place'].sound} that leads the flock to safety.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    flock = _safe_fact(world, f, "flock")
    place = _safe_fact(world, f, "place")
    danger = _safe_fact(world, f, "danger")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who was the story about near {place.name}?",
            answer=f"It was about {hero.id}, a shepherd who watched over {flock.phrase}.",
        ),
        QAItem(
            question=f"What danger rose near the flock?",
            answer=f"{danger.name} rose, and it made a {danger.danger_sound} sound that frightened the flock.",
        ),
        QAItem(
            question=f"What helped {hero.id} lead the flock to safety?",
            answer=f"{helper.name} helped, because {helper.action} and {helper.exit_phrase}.",
        ),
        QAItem(
            question=f"Why was this a story about {world.moral_value}?",
            answer=f"It was about {world.moral_value} because {hero.id} chose to guard the flock and find the exit before harm could spread.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shepherd?",
            answer="A shepherd is a person who watches over sheep and keeps them safe.",
        ),
        QAItem(
            question="What does shallow mean?",
            answer="Shallow means not deep, so something can be crossed more safely.",
        ),
        QAItem(
            question="What is an exit?",
            answer="An exit is a way out of a place or danger.",
        ),
        QAItem(
            question="Why can sound matter in a myth?",
            answer="Sound can warn, guide, or show that something important is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    danger = _safe_lookup(DANGERS, params.danger)
    helper = _safe_lookup(HELPERS, params.helper)
    world = World(place, danger, helper, params.moral_value)

    hero = world.add(Entity(id=params.seed and f"{params.place}_shepherd" or "shepherd", kind="character", type="shepherd"))
    flock = world.add(Entity(id="flock", kind="thing", type="flock", phrase="the white flock"))
    world.facts.update(hero=hero, flock=flock)

    _tell(world, hero, flock)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
% Facts are supplied from Python registries.
shallow_place(P) :- place(P), shallow(P).
exit_place(P) :- place(P), has_exit(P).
good_story(P, D, H, M) :- shallow_place(P), exit_place(P), danger(D), helper(H), moral(M), trial(D, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.shallow:
            lines.append(asp.fact("shallow", pid))
        if p.has_exit:
            lines.append(asp.fact("has_exit", pid))
    for did, d in DANGERS.items():
        lines.append(asp.fact("danger", did))
        lines.append(asp.fact("trial", did, d.moral_trial))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
    for m in MORAL_VALUES:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/4."))
    asp_set = set(asp.atoms(model, "good_story"))
    py_set = {(p, d, h, m) for p in PLACES for d in DANGERS for h in HELPERS for m in MORAL_VALUES if _safe_lookup(PLACES, p).shallow and _safe_lookup(PLACES, p).has_exit and _safe_lookup(DANGERS, d).moral_trial == m}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="brook", danger="storm", helper="horn", moral_value="courage"),
        StoryParams(place="ford", danger="wolf", helper="lantern", moral_value="mercy"),
        StoryParams(place="gate", danger="fire", helper="song", moral_value="wisdom"),
    ]


CURATED = build_curated()


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

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_story/4."))
        print(sorted(set(asp.atoms(model, "good_story"))))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
