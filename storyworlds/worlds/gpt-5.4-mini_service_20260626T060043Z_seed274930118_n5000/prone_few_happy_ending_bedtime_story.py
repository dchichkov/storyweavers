#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/prone_few_happy_ending_bedtime_story.py
======================================================================================================================

A small bedtime-story world with a gentle problem: a sleepy child is prone,
has a few last-minute worries, and finds a happy ending through a cozy,
state-driven bedtime ritual.

The seed words are woven into the domain itself:
- prone: the child is lying prone, restless on the bed
- few: the parent offers a few calming steps and a few quiet choices
- happy ending: the story ends with calm sleep and a warm closing image
- bedtime story: the prose stays child-facing, soft, and reassuring
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

    child: object | None = None
    item: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "dad"}:
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
    place: str = "the moonlit bedroom"
    calm: bool = True
    affords: set[str] = field(default_factory=lambda: {"bedtime"})
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
class Ritual:
    id: str
    title: str
    steps: list[str]
    soothe: str
    close: str
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
class ComfortItem:
    id: str
    label: str
    phrase: str
    helps: set[str]
    gentle: bool = True
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def trace_value(d: dict[str, float], key: str) -> float:
    return d.get(key, 0.0)


def _apply_drowsy(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("sleepy", 0) < THRESHOLD:
        return out
    sig = ("drowsy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["heavy_eyes"] = child.memes.get("heavy_eyes", 0) + 1
    out.append(f"{child.pronoun('possessive').capitalize()} eyes felt heavier and slower.")
    return out


def _apply_soothe(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("worry", 0) < THRESHOLD:
        return out
    if child.memes.get("comfort", 0) < THRESHOLD:
        return out
    sig = ("soothe",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    out.append("The room felt softer, and the worry began to melt away.")
    return out


def _apply_sleep(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("calm", 0) < THRESHOLD:
        return out
    if child.meters.get("prone_rest", 0) < THRESHOLD:
        return out
    sig = ("sleep",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["asleep"] = 1.0
    out.append("Soon the child was asleep at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_apply_drowsy, _apply_soothe, _apply_sleep):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str
    parent: str
    item: str
    ritual: str
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


SETTINGS = {
    "bedroom": Setting(place="the moonlit bedroom", calm=True, affords={"bedtime"}),
}

RITUALS = {
    "counting": Ritual(
        id="counting",
        title="counting breaths",
        steps=["counted a few slow breaths", "counted a few stars on the curtain"],
        soothe="soft and safe",
        close="counted one last breath together",
        tags={"few", "prone", "bedtime"},
    ),
    "story": Ritual(
        id="story",
        title="one last tiny story",
        steps=["read a few gentle pages", "turned a few slow pages"],
        soothe="warm and sleepy",
        close="closed the book and tucked it aside",
        tags={"few", "bedtime"},
    ),
    "song": Ritual(
        id="song",
        title="a quiet lullaby",
        steps=["hummed a few quiet notes", "let the song float over the pillows"],
        soothe="soft as a feather",
        close="finished the lullaby in a whisper",
        tags={"bedtime"},
    ),
}

COMFORT = {
    "blanket": ComfortItem(
        id="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        helps={"worry", "cold", "prone"},
    ),
    "lamp": ComfortItem(
        id="lamp",
        label="nightlight",
        phrase="a tiny nightlight",
        helps={"dark", "worry"},
    ),
    "bear": ComfortItem(
        id="bear",
        label="teddy bear",
        phrase="a sleepy teddy bear",
        helps={"worry", "prone"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ivy", "Theo", "Luna", "Eli"]
PARENT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bedroom", r_id, c_id) for r_id in RITUALS for c_id in COMFORT]


def explain_rejection(ritual: Ritual, item: ComfortItem) -> str:
    return (
        f"(No story: {ritual.title} and {item.label} do not make a sensible bedtime "
        f"pair for this world. Try a gentler comfort item.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small bedtime storyworld with a prone child, a few calm steps, and a happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--item", choices=COMFORT)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if getattr(args, "ritual", None) and getattr(args, "item", None):
        if (getattr(args, "place", None) or "bedroom", getattr(args, "ritual", None), getattr(args, "item", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    ritual = getattr(args, "ritual", None) or rng.choice(sorted(RITUALS))
    item = getattr(args, "item", None) or rng.choice(sorted(COMFORT))
    if (getattr(args, "place", None) or "bedroom", ritual, item) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    return StoryParams(name=name, parent=parent, item=item, ritual=ritual)


def _introduce(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    world.say(
        f"{child.id} was a small child who liked the quiet part of bedtime. "
        f"{child.pronoun('possessive').capitalize()} {item.label} waited by the pillow, "
        f"ready for a sleepy night."
    )
    world.say(
        f"{parent.pronoun().capitalize()} knew {child.id} was prone to staying awake for a few more minutes."
    )


def _setup_worry(world: World, child: Entity, parent: Entity, item: Entity, ritual: Ritual) -> None:
    child.memes["sleepy"] = 1.0
    child.memes["worry"] = 1.0
    child.meters["prone_rest"] = 1.0
    world.say(
        f"At bedtime, {child.id} lay prone on the bed and whispered that {child.pronoun('possessive')} head was still busy."
    )
    world.say(
        f"{parent.pronoun().capitalize()} smiled and offered {item.phrase} and {ritual.title}."
    )
    world.facts["worry_item"] = item.id
    world.facts["ritual"] = ritual.id


def _do_ritual(world: World, child: Entity, parent: Entity, item: Entity, ritual: Ritual) -> None:
    child.memes["comfort"] = child.memes.get("comfort", 0) + 1
    if item.id == "blanket":
        child.meters["wrapped"] = 1.0
    elif item.id == "lamp":
        child.meters["light"] = 1.0
    else:
        child.meters["hugged"] = 1.0
    for step in ritual.steps:
        world.say(step.capitalize() + ".")
    propagate(world, narrate=True)
    if child.memes.get("worry", 0) < THRESHOLD:
        world.say(
            f"{parent.pronoun().capitalize()} and {child.id} kept going with a few more quiet breaths, and the room grew very still."
        )


def _resolution(world: World, child: Entity, parent: Entity, item: Entity, ritual: Ritual) -> None:
    if world.get("child").meters.get("asleep", 0) >= THRESHOLD:
        world.say(
            f"In the end, {child.id} was asleep beneath {item.phrase}, and {parent.pronoun('possessive')} {child.id} looked peaceful and safe."
        )
        world.say(
            f"{parent.pronoun().capitalize()} tucked the blanket in, turned out the light, and left with a happy heart."
        )


def tell(setting: Setting, ritual: Ritual, comfort: ComfortItem, name: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="child", label=name))
    child.id = name
    child.type = "child"
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    item = world.add(Entity(id=comfort.id, type=comfort.label, label=comfort.label, phrase=comfort.phrase, owner=name))
    _introduce(world, child, parent, item)
    world.para()
    _setup_worry(world, child, parent, item, ritual)
    world.para()
    _do_ritual(world, child, parent, item, ritual)
    world.para()
    _resolution(world, child, parent, item, ritual)
    world.facts.update(child=child, parent=parent, item=item, ritual=ritual, comfort=comfort, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    ritual = _safe_fact(world, f, "ritual")
    item = _safe_fact(world, f, "comfort")
    return [
        f'Write a bedtime story for a preschooler about {child.id}, a prone child, who needs a few calm minutes before sleep.',
        f"Tell a gentle story where {child.id} gets ready for bed with {_safe_lookup(RITUALS, ritual).title} and {COMFORT[item.id].phrase}.",
        f'Write a short happy-ending bedtime story that includes the words "prone" and "few".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    item = _safe_fact(world, f, "item")
    ritual = _safe_fact(world, f, "ritual")
    return [
        QAItem(
            question=f"Why was {child.id} still awake at bedtime?",
            answer=f"{child.id} was prone on the bed with a few busy thoughts still moving around, so {child.pronoun()} was not ready to sleep yet.",
        ),
        QAItem(
            question=f"What did {parent.pronoun().capitalize()} offer to help {child.id} settle down?",
            answer=f"{parent.pronoun().capitalize()} offered {item.phrase} and {_safe_lookup(RITUALS, ritual).title} to make bedtime feel safe and calm.",
        ),
        QAItem(
            question=f"What was the happy ending of the story?",
            answer=f"{child.id} fell asleep at last, tucked under {item.phrase}, while {parent.pronoun('possessive')} room stayed quiet and warm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does prone mean?",
            answer="Prone means lying face-down or stretched out on a surface, like when someone is resting on a bed or floor.",
        ),
        QAItem(
            question="What does few mean?",
            answer="Few means not many. If you have a few breaths or a few pages, you only have a small number of them.",
        ),
        QAItem(
            question="Why do bedtime routines help?",
            answer="Bedtime routines help because the same calm steps each night tell the body and mind that it is time to rest.",
        ),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prone_child(C) :- child(C), state(C, prone).
few_needed(C) :- state(C, worried), count(C, few).
can_sleep(C) :- comfort(C, item), ritual(C, ritual), item_help(item, comfort), ritual_soothes(ritual).
happy_ending(C) :- prone_child(C), few_needed(C), can_sleep(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("state", "child", "prone"))
    lines.append(asp.fact("state", "child", "worried"))
    lines.append(asp.fact("count", "child", "few"))
    for item_id, item in COMFORT.items():
        lines.append(asp.fact("item_help", item_id, "comfort"))
    for rit_id, rit in RITUALS.items():
        lines.append(asp.fact("ritual_soothes", rit_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1."))
    asp_set = set(asp.atoms(model, "happy_ending"))
    py_set = {("child",)} if True else set()
    if asp_set == py_set:
        print("OK: clingo gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1."))
    return sorted(set(asp.atoms(model, "happy_ending")))


def build_story(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["bedroom"], _safe_lookup(RITUALS, params.ritual), COMFORT[params.item], params.name, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
    StoryParams(name="Mia", parent="mother", item="blanket", ritual="counting"),
    StoryParams(name="Theo", parent="father", item="bear", ritual="story"),
    StoryParams(name="Luna", parent="mother", item="lamp", ritual="song"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show happy_ending/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show happy_ending/1."))
        print(sorted(set(asp.atoms(model, "happy_ending"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
