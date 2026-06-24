#!/usr/bin/env python3
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    name: str = ""
    title: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    item: object | None = None
    def label(self) -> str:
        return self.title or self.name or self.id

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "goddess", "sister"}
        male = {"boy", "man", "father", "king", "god", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
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


@dataclass
class Place:
    id: str
    name: str
    kind: str
    echoes: bool = False
    dark: bool = False
    sacred: bool = False
    winds: bool = False
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
class Sound:
    id: str
    word: str
    effect: str
    can_call: bool = False
    can_answer: bool = False
    can_warn: bool = False
    can_help: bool = False
    can_bind: bool = False
    can_open: bool = False
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
class Artifact:
    id: str
    label: str
    type: str
    holds: str
    guarded_by: str
    shines: bool = False
    sealed: bool = False
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    guide: str
    guide_type: str
    sound: str
    artifact: str
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


PLACES = {
    "cave": Place(id="cave", name="the cave", kind="cave", echoes=True, dark=True),
    "temple": Place(id="temple", name="the temple", kind="temple", echoes=True, sacred=True),
    "forest": Place(id="forest", name="the forest", kind="forest", winds=True),
}

SOUNDS = {
    "drum": Sound(id="drum", word="drum", effect="BOOM-BOOM", can_call=True, can_warn=True, can_open=True),
    "bell": Sound(id="bell", word="bell", effect="ding-ding", can_call=True, can_answer=True, can_help=True),
    "flute": Sound(id="flute", word="flute", effect="toooo", can_answer=True, can_bind=True),
    "thunder": Sound(id="thunder", word="thunder", effect="KRA-KOOM", can_warn=True, can_open=True),
    "chime": Sound(id="chime", word="chime", effect="ting-ting", can_call=True, can_help=True, can_bind=True),
}

ARTIFACTS = {
    "gate": Artifact(id="gate", label="stone gate", type="gate", holds="lost road", guarded_by="call", sealed=True),
    "spring": Artifact(id="spring", label="hidden spring", type="spring", holds="bright water", guarded_by="answer"),
    "vow": Artifact(id="vow", label="old vow", type="vow", holds="peace", guarded_by="bind"),
}

HERO_NAMES = ["Ari", "Mara", "Niko", "Sera", "Ivo", "Lina"]
GUIDE_NAMES = ["Elder Oren", "Mother Sky", "Old River", "Aunt Ember", "Brother Ash"]
TYPES = ["girl", "boy", "woman", "man"]


def reasonableness_gate(place: Place, sound: Sound, artifact: Artifact) -> bool:
    if artifact.guarded_by == "call":
        return sound.can_call and place.echoes
    if artifact.guarded_by == "answer":
        return sound.can_answer and (place.sacred or place.echoes)
    if artifact.guarded_by == "bind":
        return sound.can_bind and (place.winds or place.sacred or place.echoes)
    return False


def explain_rejection(place: Place, sound: Sound, artifact: Artifact) -> str:
    return (
        f"(No story: {sound.word} cannot fairly unlock the {artifact.label} in {place.name}. "
        f"The sound and the guard do not match.)"
    )


def _act_call(world: World, hero: Entity, sound: Sound, artifact: Artifact) -> None:
    if sound.can_call and world.place.echoes and artifact.guarded_by == "call":
        sig = ("call", artifact.id, sound.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        artifact.sealed = False
        world.facts["opened"] = True
        world.say(f"At once, {sound.effect} rolled through {world.place.name}, and the {artifact.label} answered.")
        world.say(f"The stone turned with a soft sigh, as if it had been waiting for {hero.label()} to speak.")
        return


def _act_answer(world: World, guide: Entity, sound: Sound, artifact: Artifact) -> None:
    if sound.can_answer and (world.place.sacred or world.place.echoes) and artifact.guarded_by == "answer":
        sig = ("answer", artifact.id, sound.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        artifact.sealed = False
        world.facts["opened"] = True
        world.say(f'"{sound.word.capitalize()}," said {guide.label()}, and the air replied with {sound.effect}.')
        world.say(f'The hidden spring woke beneath the floor, because a true answer had found it.')
        return


def _act_bind(world: World, hero: Entity, guide: Entity, sound: Sound, artifact: Artifact) -> None:
    if sound.can_bind and (world.place.winds or world.place.sacred or world.place.echoes) and artifact.guarded_by == "bind":
        sig = ("bind", artifact.id, sound.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        artifact.sealed = False
        world.facts["opened"] = True
        hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
        world.say(f'"{sound.word.capitalize()}," whispered {hero.label()}, and {guide.label()} answered, "So it shall be."')
        world.say(f'Then {sound.effect} wound around them like a ribbon, and the old vow softened into peace.')
        return


def tell(place: Place, hero_name: str, hero_type: str, guide_name: str, guide_type: str, sound: Sound, artifact: Artifact) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, name=hero_name, title=hero_name))
    guide = world.add(Entity(id="guide", kind="character", type=guide_type, name=guide_name, title=guide_name))
    item = world.add(Entity(id="artifact", type=artifact.type, title=artifact.label))

    world.say(f"{hero.label()} came to {place.name} with {guide.label()}, where the old stones listened.")
    world.say(f"{guide.label()} said, \"If you want the way to open, speak the sound of the world: {sound.word}.\"")
    world.say(f'{hero.label()} breathed in and called, "Dialogue."')
    world.say(f"Then came {sound.effect}.")

    world.para()
    if artifact.guarded_by == "call":
        world.say(f"{hero.label()} asked, \"Will you open for us?\"")
        _act_call(world, hero, sound, item)
    elif artifact.guarded_by == "answer":
        world.say(f"{guide.label()} asked, \"What lives in the dark and wakes when it is named?\"")
        _act_answer(world, guide, sound, item)
    else:
        world.say(f"{hero.label()} said, \"We will keep faith.\"")
        _act_bind(world, hero, guide, sound, item)

    world.para()
    if not world.facts.get("opened"):
        pass
    world.say(f"At last, the {artifact.label} opened, and the path inside was no longer lost.")
    world.say(f"{hero.label()} and {guide.label()} went home with the sound still shining in their ears.")
    world.facts.update(hero=hero, guide=guide, sound=sound, artifact=item, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    sound = _safe_fact(world, f, "sound")
    artifact = _safe_fact(world, f, "artifact")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short myth for a child where "{sound.word}" is spoken in {place.name} and something sealed opens.',
        f"Tell a gentle mythic story with dialogue in which {hero.label()} and {guide.label()} use {sound.effect} to help the {artifact.label} awaken.",
        f"Write a tiny legend about a traveler, a wise guide, and the sound word {sound.word}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    sound = _safe_fact(world, f, "sound")
    artifact = _safe_fact(world, f, "artifact")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who came to {place.name} and spoke the sound word {sound.word}?",
            answer=f"{hero.label()} came with {guide.label()}, and {hero.label()} spoke the sound word {sound.word}.",
        ),
        QAItem(
            question=f"What did the guide say would help the {artifact.label} open?",
            answer=f"{guide.label()} said that speaking {sound.word} would help the {artifact.label} open.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The {artifact.label} opened, and {hero.label()} and {guide.label()} left with the path no longer lost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(
        [
            QAItem(
                question="What is an echo?",
                answer="An echo is a sound that comes back after it bounces off walls, cliffs, or other hard things.",
            ),
            QAItem(
                question="Why do people use a drum in a story?",
                answer="A drum can sound strong and important, so it can call attention or mark a big moment.",
            ),
            QAItem(
                question="What does it mean to keep a vow?",
                answer="To keep a vow means to do what you promised and not break your word.",
            ),
        ]
    )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = [f"--- trace: {world.place.name} ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} title={e.title!r} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cave", hero="Ari", hero_type="boy", guide="Elder Oren", guide_type="man", sound="drum", artifact="gate"),
    StoryParams(place="temple", hero="Mara", hero_type="girl", guide="Mother Sky", guide_type="woman", sound="bell", artifact="spring"),
    StoryParams(place="forest", hero="Niko", hero_type="boy", guide="Aunt Ember", guide_type="woman", sound="chime", artifact="vow"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic storyworld with dialogue and sound effects.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--guide")
    ap.add_argument("--guide-type", choices=TYPES)
    ap.add_argument("--sound", choices=sorted(SOUNDS))
    ap.add_argument("--artifact", choices=sorted(ARTIFACTS))
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    sound = getattr(args, "sound", None) or rng.choice(sorted(SOUNDS))
    artifact = getattr(args, "artifact", None) or rng.choice(sorted(ARTIFACTS))
    p = _safe_lookup(PLACES, place)
    s = _safe_lookup(SOUNDS, sound)
    a = _safe_lookup(ARTIFACTS, artifact)
    if not reasonableness_gate(p, s, a):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    guide_type = getattr(args, "guide_type", None) or rng.choice(["woman", "man"])
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(GUIDE_NAMES)
    return StoryParams(place=place, hero=hero, hero_type=hero_type, guide=guide, guide_type=guide_type, sound=sound, artifact=artifact)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), params.hero, params.hero_type, params.guide, params.guide_type, _safe_lookup(SOUNDS, params.sound), _safe_lookup(ARTIFACTS, params.artifact))
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


ASP_RULES = r"""
place(cave;temple;forest).
sound(drum;bell;flute;thunder;chime).
artifact(gate;spring;vow).

echo_place(cave).
echo_place(temple).
wind_place(forest).
sacred_place(temple).

call_sound(drum).
call_sound(bell).
call_sound(chime).

answer_sound(bell).
answer_sound(flute).
answer_sound(chime).

bind_sound(flute).
bind_sound(chime).

guarded_by(gate,call).
guarded_by(spring,answer).
guarded_by(vow,bind).

can_open(P,S,A) :- guarded_by(A,call), echo_place(P), call_sound(S).
can_open(P,S,A) :- guarded_by(A,answer), (echo_place(P); sacred_place(P)), answer_sound(S).
can_open(P,S,A) :- guarded_by(A,bind), (echo_place(P); sacred_place(P); wind_place(P)), bind_sound(S).

#show can_open/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.echoes:
            lines.append(asp.fact("echo_place", p.id))
        if p.sacred:
            lines.append(asp.fact("sacred_place", p.id))
        if p.winds:
            lines.append(asp.fact("wind_place", p.id))
    for s in SOUNDS.values():
        lines.append(asp.fact("sound", s.id))
        if s.can_call:
            lines.append(asp.fact("call_sound", s.id))
        if s.can_answer:
            lines.append(asp.fact("answer_sound", s.id))
        if s.can_bind:
            lines.append(asp.fact("bind_sound", s.id))
    for a in ARTIFACTS.values():
        lines.append(asp.fact("artifact", a.id))
        lines.append(asp.fact("guarded_by", a.id, a.guarded_by))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_open/3."))
    asp_set = set(asp.atoms(model, "can_open"))
    py_set = set()
    for p in PLACES.values():
        for s in SOUNDS.values():
            for a in ARTIFACTS.values():
                if reasonableness_gate(p, s, a):
                    py_set.add((p.id, s.id, a.id))
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_open/3."))
    return sorted(set(asp.atoms(model, "can_open")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show can_open/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
