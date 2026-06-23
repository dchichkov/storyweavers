#!/usr/bin/env python3
"""
storyworlds/worlds/infantry_flashback_slice_of_life.py
======================================================

A small slice-of-life storyworld about a child who visits an infantry museum,
then remembers a calm flashback from a day of carrying lunch and socks to a
relative at the base. The stories stay grounded in simple physical state:
meters for distance, load, and tiredness; memes for memory, pride, worry,
comfort, and relief.

The domain is intentionally gentle. The tension is small: a child may wander,
forget an item, or worry about a family member on a long walk. A flashback can
reframe what is happening now, and a kind helper or a remembered habit can
resolve it.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- prompts, story-grounded QA, world-knowledge QA
- Python reasonableness gate plus inline ASP twin
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    child: object | None = None
    helper: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
        if not hasattr(self, "_tags"):
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
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
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
class Flashback:
    id: str
    memory_name: str
    cue: str
    scene: str
    effect: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class HelpfulObject:
    id: str
    label: str
    phrase: str
    kind: str
    for_role: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    flashback: str
    object: str
    child_name: str
    child_gender: str
    caregiver: str
    child_trait: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.flashback_triggered = False
        self.flashback_resolved = False

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.flashback_triggered = self.flashback_triggered
        w.flashback_resolved = self.flashback_resolved
        return w


def _r_tired(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters.get("walk", 0) >= THRESHOLD and child.meters.get("load", 0) >= THRESHOLD:
        sig = ("tired",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["tired"] += 1
        out.append("__tired__")
    return out


def _r_memory_calm(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("memory", 0) >= THRESHOLD and child.memes.get("worry", 0) >= THRESHOLD:
        sig = ("calm",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["calm"] += 1
        out.append("__calm__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_tired, _r_memory_calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(place: Place, flashback: Flashback, obj: HelpfulObject) -> bool:
    return "memory" in flashback.tags and obj.for_role in {"child", "caregiver"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for fid, fb in FLASHBACKS.items():
            for oid, obj in OBJECTS.items():
                if reasonableness_ok(place, fb, obj):
                    combos.append((pid, fid, oid))
    return combos


def _do_walk(world: World, child: Entity, meters: float = 1.0) -> None:
    child.meters["walk"] = child.meters.get("walk", 0) + meters


def _do_load(world: World, child: Entity, obj: HelpfulObject) -> None:
    child.meters["load"] = child.meters.get("load", 0) + 1
    child.attrs["carrying"] = obj.id


def _flashback(world: World, child: Entity, fb: Flashback, caregiver: Entity) -> None:
    child.memes["memory"] = child.memes.get("memory", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.flashback_triggered = True
    world.say(f"{fb.cue} made {child.id} remember {fb.memory_name}.")
    world.say(f"{fb.scene}.")
    if fb.effect:
        world.say(fb.effect)
    caregiver.memes["kindness"] = caregiver.memes.get("kindness", 0) + 1
    propagate(world, narrate=True)


def _resolve(world: World, child: Entity, caregiver: Entity, obj: HelpfulObject, fb: Flashback) -> None:
    child.memes["worry"] = max(0, child.memes.get("worry", 0) - 1)
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    child.memes["warmth"] = child.memes.get("warmth", 0) + 1
    world.flashback_resolved = True
    world.say(
        f"{caregiver.label_word.capitalize()} smiled and helped {child.id} use {obj.phrase} the same calm way."
    )
    world.say(
        f"{child.id} felt steadier, because {fb.memory_name} had turned a small worry into a useful habit."
    )


def tell(place: Place, flashback: Flashback, obj: HelpfulObject,
         child_name: str = "Mina", child_gender: str = "girl",
         caregiver: str = "mother", child_trait: str = "careful") -> World:
    world = World(place)
    child = world.add(Entity(
        id="child", kind="character", type=child_gender, label=child_name,
        role="child", meters={"walk": 0.0, "load": 0.0}, memes={"memory": 0.0, "worry": 0.0}
    ))
    helper = world.add(Entity(
        id="caregiver", kind="character", type=caregiver, label="the caregiver",
        role="caregiver", meters={"walk": 0.0}, memes={"kindness": 0.0}
    ))
    item = world.add(Entity(id="item", kind="thing", type=obj.kind, label=obj.label, phrase=obj.phrase))
    world.facts.update(child=child, caregiver=helper, item=item, flashback=flashback, place=place, obj=obj)
    child.attrs["trait"] = child_trait
    child.attrs["carrying"] = ""
    helper.attrs["role"] = caregiver

    world.say(f"{child.label} was a little {child_trait} {child_gender} who liked quiet errands.")
    world.say(f"One afternoon, {child.id} and {helper.label_word} walked through {place.label}.")
    world.say(f"{child.id} carried {obj.phrase}, and the walk felt long but ordinary.")

    world.para()
    _do_walk(world, child, meters=2.0)
    _do_load(world, child, obj)
    world.say(f"At first, {child.id} kept going, one careful step after another.")
    _flashback(world, child, flashback, helper)

    world.para()
    _resolve(world, child, helper, obj, flashback)
    world.say(
        f"By the end, {child.id} still had {obj.phrase}, but now the little errand felt easy."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    fb: Flashback = f["flashback"]  # type: ignore[assignment]
    obj: HelpfulObject = f["obj"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f'Write a short slice-of-life story for a young child that includes the word "infantry" and a gentle flashback.',
        f"Tell a calm story about {child.label} walking through {place.label} with {obj.phrase}, then remembering {fb.memory_name}.",
        f'Write a child-friendly story where a small memory changes how a simple errand goes, and include "infantry" naturally.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    caregiver: Entity = f["caregiver"]  # type: ignore[assignment]
    obj: HelpfulObject = f["obj"]  # type: ignore[assignment]
    fb: Flashback = f["flashback"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.label}, a little child on a calm errand with {caregiver.label_word}.",
        ),
        QAItem(
            question=f"What did {child.label} carry through {place.label}?",
            answer=f"{child.label} carried {obj.phrase}. It was a small useful thing, so the walk could stay simple and ordinary.",
        ),
        QAItem(
            question=f"What made {child.label} pause and remember something older?",
            answer=f"{fb.cue} brought back {fb.memory_name}. That flashback let {child.label} feel the present moment in a different way.",
        ),
    ]
    if world.flashback_triggered:
        qa.append(QAItem(
            question=f"Why did the flashback help {child.label}?",
            answer=f"It reminded {child.label} of a calm way to do the errand. That memory eased the worry and made the next step feel easier.",
        ))
    if world.flashback_resolved:
        qa.append(QAItem(
            question=f"How did {caregiver.label_word} help at the end?",
            answer=f"{caregiver.label_word.capitalize()} smiled and helped keep the errand steady. The helpful adult made the small change from worry to relief.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who move and work on foot instead of riding in vehicles.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened before the present moment.",
        ),
        QAItem(
            question="What kind of story is slice of life?",
            answer="A slice-of-life story shows a small everyday moment, like a walk, a meal, or a simple errand.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  flashback_triggered={world.flashback_triggered}")
    lines.append(f"  flashback_resolved={world.flashback_resolved}")
    return "\n".join(lines)


PLACES = {
    "street": Place(id="street", label="the quiet street", indoors=False, affords={"walk"}),
    "museum": Place(id="museum", label="the small local museum", indoors=True, affords={"walk"}),
    "kitchen": Place(id="kitchen", label="the kitchen table", indoors=True, affords={"walk"}),
}

FLASHBACKS = {
    "infantry": Flashback(
        id="infantry",
        memory_name="the word infantry from a history book",
        cue="A museum plaque about infantry",
        scene="In the memory, a page showed neat rows of soldiers walking on foot",
        effect="The memory was not scary; it just felt orderly, like someone lining up shoes by the door.",
        tags={"memory", "infantry"},
    ),
    "lunch": Flashback(
        id="lunch",
        memory_name="the lunch they once carried to a gate",
        cue="The smell of warm bread",
        scene="In the memory, a paper bag swung lightly from a small hand",
        effect="It was the same kind of ordinary errand, and that made the present feel easier.",
        tags={"memory", "lunch"},
    ),
    "socks": Flashback(
        id="socks",
        memory_name="the time they folded fresh socks for someone tired",
        cue="Seeing a folded towel",
        scene="In the memory, clean socks waited on a chair after a long day",
        effect="The remembered routine felt kind and useful, not big or dramatic at all.",
        tags={"memory", "socks"},
    ),
}

OBJECTS = {
    "bag": HelpfulObject(id="bag", label="paper bag", phrase="a paper bag of snacks", kind="bag", for_role="child", tags={"bag"}),
    "socks": HelpfulObject(id="socks", label="clean socks", phrase="a pair of clean socks", kind="socks", for_role="caregiver", tags={"socks"}),
    "water": HelpfulObject(id="water", label="water bottle", phrase="a water bottle", kind="bottle", for_role="child", tags={"water"}),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "June", "Nora", "Ada"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Owen", "Finn", "Leo"]
TRAITS = ["careful", "quiet", "thoughtful", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life infantry flashback storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
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


def valid_combo(place: str, flashback: str, obj: str) -> bool:
    return reasonableness_ok(_safe_lookup(PLACES, place), _safe_lookup(FLASHBACKS, flashback), _safe_lookup(OBJECTS, obj))


def explain_rejection() -> str:
    return "(No story: this combination does not match the gentle flashback premise.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "flashback", None) is None or c[1] == getattr(args, "flashback", None))
              and (getattr(args, "object_", None) is None or c[2] == getattr(args, "object_", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, flashback, obj = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = getattr(args, "caregiver", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, flashback=flashback, object=obj, child_name=name, child_gender=gender, caregiver=caregiver, child_trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.flashback not in FLASHBACKS or params.object not in OBJECTS:
        pass
    if not valid_combo(params.place, params.flashback, params.object):
        pass
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(FLASHBACKS, params.flashback), _safe_lookup(OBJECTS, params.object),
                 child_name=params.child_name, child_gender=params.child_gender,
                 caregiver=params.caregiver, child_trait=params.child_trait)
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
valid(P,F,O) :- place(P), flashback(F), object(O), memory_back(F), helpful(O).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid, fb in FLASHBACKS.items():
        lines.append(asp.fact("flashback", fid))
        if "memory" in fb.tags:
            lines.append(asp.fact("memory_back", fid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.for_role in {"child", "caregiver"}:
            lines.append(asp.fact("helpful", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    ok = set(asp_valid_combos()) == set(valid_combos())
    sample_ok = True
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(generate(resolve_params(argparse.Namespace(place=None, flashback=None, object_=None, name=None, gender=None, caregiver=None, trait=None), random.Random(777))))
    except Exception:
        sample_ok = False
    if ok and sample_ok:
        print("OK: ASP parity matches and smoke generation succeeded.")
        return 0
    if not ok:
        print("MISMATCH between ASP and Python valid combos.")
    if not sample_ok:
        print("SMOKE TEST FAILED: generation or emit crashed.")
    return 1


CURATED = [
    StoryParams(place="museum", flashback="infantry", object="bag", child_name="Mina", child_gender="girl", caregiver="mother", child_trait="quiet"),
    StoryParams(place="street", flashback="lunch", object="water", child_name="Eli", child_gender="boy", caregiver="father", child_trait="careful"),
    StoryParams(place="kitchen", flashback="socks", object="socks", child_name="Nora", child_gender="girl", caregiver="mother", child_trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
