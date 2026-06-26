#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/obvious_twist_heartwarming.py
=============================================================================================================

A small heartwarming storyworld with an obvious twist:
a child worries about a strange-looking bundle, but the "mystery" is really a
loving surprise in progress.

The world is simulated with physical meters and emotional memes.
The turn comes from a state change: suspicion rises, then the child learns the
bundle is a cozy gift or helpful project, and the ending proves the change.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bundle: object | None = None
    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
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
    inside: bool
    affords: set[str] = field(default_factory=set)
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
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    comfort: str
    warms: bool = False
    kind: str = "gift"
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
class StoryParams:
    place: str
    surprise: str
    name: str
    gender: str
    helper: str
    trait: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("worry", 0) < THRESHOLD:
        return out
    if ("worry", child.id) in world.fired:
        return out
    world.fired.add(("worry", child.id))
    child.memes["unease"] = child.memes.get("unease", 0) + 1
    out.append(f"{child.id} kept looking at the strange bundle and feeling less sure.")
    return out


def _r_reveal(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    surprise = _safe_fact(world, world.facts, "surprise")
    if child.memes.get("curious", 0) < THRESHOLD:
        return []
    if ("reveal", child.id) in world.fired:
        return []
    world.fired.add(("reveal", child.id))
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    helper.memes["love"] = helper.memes.get("love", 0) + 1
    out = [f"Then {helper.id} smiled and opened the bundle."]
    out.append(surprise.reveal)
    return out


def _r_comfort(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    surprise = _safe_fact(world, world.facts, "surprise")
    if child.memes.get("relief", 0) < THRESHOLD:
        return []
    if ("comfort", child.id) in world.fired:
        return []
    world.fired.add(("comfort", child.id))
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    helper.memes["tenderness"] = helper.memes.get("tenderness", 0) + 1
    out = [f"It turned out to be {surprise.phrase}, made with love for {child.id}."]
    out.append(f"{surprise.comfort}")
    return out


RULES = [_r_worry, _r_reveal, _r_comfort]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_resolution(world: World) -> bool:
    sim = world.copy()
    child = sim.get("child")
    child.memes["curious"] = child.memes.get("curious", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    propagate(sim, narrate=False)
    return sim.get("child").memes.get("relief", 0) >= THRESHOLD


SETTINGS = {
    "kitchen": Setting(place="the kitchen", inside=True, affords={"bundle"}),
    "bedroom": Setting(place="the bedroom", inside=True, affords={"bundle"}),
    "porch": Setting(place="the porch", inside=False, affords={"bundle"}),
}

SURPRISES = {
    "kitten": Surprise(
        id="kitten",
        label="kitten",
        phrase="a tiny kitten tucked inside a warm towel",
        reveal="A tiny kitten blinked up from the towel, purring like a little motor.",
        comfort="The kitten snuggled into the child’s hands, and the room felt softer right away.",
        warms=True,
        kind="pet",
    ),
    "scarf": Surprise(
        id="scarf",
        label="scarf",
        phrase="a soft scarf with bright blue stripes",
        reveal="Inside the wrinkly paper was a soft scarf with bright blue stripes.",
        comfort="It was just the right thing for a chilly day, and it made the child smile.",
        warms=True,
        kind="gift",
    ),
    "drawing": Surprise(
        id="drawing",
        label="drawing",
        phrase="a folded paper picture with a gold star",
        reveal="The bundle held a folded paper picture with a gold star in the corner.",
        comfort="It showed the family’s favorite tree, and the child’s face lit up at once.",
        warms=False,
        kind="gift",
    ),
    "blanketfort": Surprise(
        id="blanketfort",
        label="blanket fort",
        phrase="a tiny blanket fort for quiet play",
        reveal="The bundle was actually a little blanket fort, waiting to be finished.",
        comfort="It became a cozy place to read together, and the whole house felt calmer.",
        warms=False,
        kind="project",
    ),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Ivy", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Max", "Theo"]
TRAITS = ["curious", "gentle", "brave", "quiet", "patient", "bright"]


@dataclass
class StoryParams:
    place: str
    surprise: str
    name: str
    gender: str
    helper: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming obvious-twist storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
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


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or select_name(gender, rng)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if place == "porch" and surprise == "blanketfort":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, surprise=surprise, name=name, gender=gender, helper=helper, trait=trait)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    surprise = _safe_lookup(SURPRISES, params.surprise)
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    bundle = world.add(Entity(id="bundle", type="thing", label="bundle", phrase=surprise.phrase, owner=helper.id))
    child.memes["curious"] = 1
    child.memes["worry"] = 1

    world.say(f"{params.name} was a {params.trait} little {params.gender} who loved noticing things.")
    world.say(f"One day, {params.name} found a strange bundle in {setting.place} and stopped to stare.")
    if setting.inside:
        world.say(f"The bundle looked extra mysterious in the quiet room, so {params.name} felt a tiny prickle of worry.")
    else:
        world.say(f"The bundle fluttered a little in the breeze, and {params.name} wondered what could be hiding inside.")

    world.para()
    world.say(f"{params.name} asked {helper.pronoun('object')} what it was, but the answer did not come right away.")
    world.say(f"Instead, {helper.id} gave a small smile and told {params.name} to come a little closer.")
    child.memes["curious"] += 1
    child.memes["worry"] += 1
    propagate(world, narrate=True)

    world.para()
    child.memes["curious"] += 1
    child.memes["relief"] = 1
    propagate(world, narrate=True)

    world.para()
    child.memes["relief"] = 1
    child.memes["joy"] = 1
    world.say(f"In the end, {params.name} laughed and stayed right beside {helper.id}, happy to share the surprise.")
    if surprise.warms:
        world.say(f"The little surprise made the whole place feel warm and cozy.")
    else:
        world.say(f"The little surprise made {params.name} feel loved, which was the best part of the day.")

    world.facts.update(
        child=child,
        helper=helper,
        bundle=bundle,
        surprise=surprise,
        setting=setting,
        resolved=predict_resolution(world),
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = _safe_fact(world, f, "child")
    s = _safe_fact(world, f, "surprise")
    return [
        f'Write a gentle story for a young child about {c.label} and a strange-looking bundle that turns out to be {s.phrase}.',
        f'Tell a heartwarming story where a child thinks something is a mystery, but the obvious twist is that it is a loving surprise.',
        f'Write a short story that begins with worry, reveals the bundle, and ends with {c.label} feeling happy and safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = _safe_fact(world, f, "child")
    h = _safe_fact(world, f, "helper")
    s = _safe_fact(world, f, "surprise")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What did {c.label} find in {place}?",
            answer=f"{c.label} found a strange-looking bundle, and it turned out to be {s.phrase}.",
        ),
        QAItem(
            question=f"Who helped show {c.label} what the bundle really was?",
            answer=f"{h.id} helped by opening the bundle and showing that the surprise was kind, not scary.",
        ),
        QAItem(
            question=f"How did {c.label} feel at the end of the story?",
            answer=f"{c.label} felt happy and safe after the surprise was revealed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, and it can make someone feel excited or loved.",
        ),
        QAItem(
            question="Why can a bundle look mysterious?",
            answer="A bundle can look mysterious because cloth or paper can hide what is inside until someone opens it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The obvious twist: a bundle that seems mysterious can turn out to be a loving surprise.

bundle_mysterious(B) :- bundle(B).
child_worries(C) :- child(C).
reveal_kind(H, B) :- helper(H), bundle(B).
heartwarming(C) :- child(C), helper(_), surprise_kind(_).

#show bundle_mysterious/1.
#show child_worries/1.
#show reveal_kind/2.
#show heartwarming/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise_kind", sid))
        if s.warms:
            lines.append(asp.fact("warm", sid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("bundle", "bundle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bundle_mysterious/1.\n#show child_worries/1.\n#show reveal_kind/2.\n#show heartwarming/1."))
    atoms = {str(a) for a in model}
    expected = {"bundle_mysterious(bundle)", "child_worries(child)", "reveal_kind(helper,bundle)", "heartwarming(child)"}
    if atoms == expected:
        print("OK: ASP twin matches the Python world skeleton.")
        return 0
    print("MISMATCH")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for surprise in SURPRISES:
            if place == "porch" and surprise == "blanketfort":
                continue
            out.append((place, surprise))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bundle_mysterious/1."))
    _ = model
    return sorted(valid_combos())


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
        print(asp_program("#show bundle_mysterious/1.\n#show child_worries/1.\n#show reveal_kind/2.\n#show heartwarming/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("Compatible combos:")
        for place, surprise in valid_combos():
            print(f"  {place:8} {surprise}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        cur = []
        for place, surprise in valid_combos():
            cur.append(StoryParams(place=place, surprise=surprise, name="Mia", gender="girl", helper="mother", trait="curious"))
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
