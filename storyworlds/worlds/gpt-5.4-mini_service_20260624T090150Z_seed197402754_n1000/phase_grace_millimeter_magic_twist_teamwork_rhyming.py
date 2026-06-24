#!/usr/bin/env python3
"""
storyworlds/worlds/phase_grace_millimeter_magic_twist_teamwork_rhyming.py
=========================================================================

A small rhyming storyworld about a tiny magic act, a twisty mistake, and a
teamwork fix measured in millimeters.

Seed-tale inspiration:
---
Grace loved magic. She and her little brother Finn were building a tiny stage
for a school show. Finn wanted a twisty ribbon trick, but the stage plank had a
millimeter-sized crack. Grace worried the wand would tip. Finn tried to fix it
alone, but the plank still wobbled. Then they worked together: Grace held the
plank, Finn slid in a tiny wooden shim, and the magic trick shone bright.
---

This world turns that premise into a stateful simulation:
- a tiny stage plank can wobble if the gap is too large;
- one character may want to rush ahead in a later phase;
- teamwork can close the gap and make the trick safe;
- the prose is authored to rhyme lightly and end with a clear changed image.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    fix: object | None = None
    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the workshop"
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
class Object:
    id: str
    label: str
    phrase: str
    role: str
    risk: str
    affects: str
    safe_gap_mm: int
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
class Fix:
    id: str
    label: str
    method: str
    tail: str
    can_close_mm: int
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
        clone = World(self.place)
        import copy as _copy

        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    object_id: str
    fix_id: str
    gap_mm: int
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "workshop": Place(place="the workshop", affords={"magic", "twist", "teamwork", "measure"}),
    "garden": Place(place="the garden shed", affords={"magic", "twist", "teamwork", "measure"}),
}

OBJECTS = {
    "stage": Object(
        id="stage",
        label="stage plank",
        phrase="a smooth little stage plank",
        role="magic trick stage",
        risk="wobble",
        affects="tip",
        safe_gap_mm=2,
    ),
    "wand": Object(
        id="wand",
        label="wand stand",
        phrase="a slim wand stand",
        role="magic wand stand",
        risk="tilt",
        affects="tip",
        safe_gap_mm=1,
    ),
}

FIXES = {
    "shim": Fix(
        id="shim",
        label="wooden shim",
        method="slid in a tiny wooden shim",
        tail="the little gap grew snug and neat",
        can_close_mm=3,
    ),
    "glue": Fix(
        id="glue",
        label="glue strip",
        method="pressed in a thin glue strip",
        tail="the seam held tight, not weak or beat",
        can_close_mm=2,
    ),
}

GIRL_NAMES = ["Grace", "Mia", "Luna", "Ivy", "Ella"]
BOY_NAMES = ["Finn", "Noah", "Leo", "Sam", "Owen"]


def safe_story(place: Place, gap_mm: int, obj: Object, fix: Fix) -> bool:
    return gap_mm > 0 and gap_mm <= obj.safe_gap_mm and gap_mm <= fix.can_close_mm


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(BOY_NAMES)
    object_id = getattr(args, "object", None) or "stage"
    fix_id = getattr(args, "fix", None) or "shim"
    gap_mm = getattr(args, "gap_mm", None) if getattr(args, "gap_mm", None) is not None else rng.choice([1, 2, 3])
    obj = _safe_lookup(OBJECTS, object_id)
    fix = _safe_lookup(FIXES, fix_id)

    if gap_mm <= 0:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if gap_mm > obj.safe_gap_mm and gap_mm > fix.can_close_mm:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, helper=helper, object_id=object_id, fix_id=fix_id, gap_mm=gap_mm)


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="boy", label=params.helper))
    obj = world.add(Entity(id=params.object_id, type="thing", label=_safe_lookup(OBJECTS, params.object_id).label))
    fix = world.add(Entity(id=params.fix_id, type="thing", label=_safe_lookup(FIXES, params.fix_id).label))

    obj.meters["gap_mm"] = float(params.gap_mm)
    obj.meters["wobble"] = 1.0 if params.gap_mm > obj.safe_gap_mm else 0.0
    hero.memes["hope"] = 1.0
    helper.memes["eager"] = 1.0
    world.facts.update(hero=hero, helper=helper, obj=obj, fix=fix, params=params)
    return world


def narrator_line(hero: Entity, helper: Entity, place: Place) -> str:
    return (
        f"In {place.place}, {hero.label} had a magic spark and a grin so bright; "
        f"{helper.label} came close with a twisty delight."
    )


def setup_lines(world: World) -> None:
    f = world.facts
    hero, helper, obj, params = f["hero"], f["helper"], f["obj"], f["params"]
    obj_cfg = _safe_lookup(OBJECTS, params.object_id)

    world.say(narrator_line(hero, helper, world.place))
    world.say(
        f"They planned a small show in a careful first phase, with a ribbon for sparkle and a wand for amaze."
    )
    world.say(
        f"But {obj.label} had a {params.gap_mm} millimeter crack, and that tiny odd seam could make the trick lean back."
    )
    world.say(
        f"{hero.label} said, \"If it wobbles, the wand may not twirl,\" and the little stage shivered like a shell on a whirl."
    )
    world.facts["risk"] = obj_cfg.risk


def tension_lines(world: World) -> None:
    f = world.facts
    hero, helper, obj, params = f["hero"], f["helper"], f["obj"], f["params"]
    obj_cfg = _safe_lookup(OBJECTS, params.object_id)

    world.para()
    world.say(
        f"{helper.label} tried a quick twist alone, with a brave little frown, but the plank still gave way with a creak and a down."
    )
    if params.gap_mm > obj_cfg.safe_gap_mm:
        world.say(
            f"That gap was too large for a solo fix song; the trick could go tumbling if they hurried along."
        )
    else:
        world.say(
            f"That gap was small but still tricky to tune; without teamwork, wobbling might come too soon."
        )
    world.say(
        f"{hero.label} held up a hand and said, \"Let us not race; we need teamwork and grace, and a calmer pace.\""
    )


def resolution_lines(world: World) -> None:
    f = world.facts
    hero, helper, obj, fix, params = f["hero"], f["helper"], f["obj"], f["fix"], f["params"]
    obj_cfg = _safe_lookup(OBJECTS, params.object_id)
    fix_cfg = _safe_lookup(FIXES, params.fix_id)

    if params.gap_mm <= fix_cfg.can_close_mm:
        world.para()
        world.say(
            f"Then both of them worked in a gentle, bright way: {hero.label} held the plank steady, and {helper.label} did not stray."
        )
        world.say(
            f"{fix_cfg.method}, and {fix_cfg.tail}; the tiny crack softened, and the stage felt stout and hale."
        )
        obj.meters["gap_mm"] = 0.0
        obj.meters["wobble"] = 0.0
        hero.memes["grace"] = 1.0
        helper.memes["teamwork"] = 1.0
        world.facts["resolved"] = True
        world.say(
            f"At last came the magic twist, neat as a rhyme: the ribbon spun rosy, the wand chimed on time."
        )
        world.say(
            f"{hero.label} bowed with a smile, and {helper.label} cheered near; the stage stood so steady it seemed to glow clear."
        )
    else:
        world.para()
        world.say(
            f"They looked for another way, with grace in their eyes, because the first tiny fix could not reach that size."
        )
        world.say(
            f"So they chose teamwork again and again at the seam, until the wobble went quiet and steadied the dream."
        )
        obj.meters["gap_mm"] = 0.0
        obj.meters["wobble"] = 0.0
        world.facts["resolved"] = True
        world.say(
            f"The magic twist worked at last, soft and sweet; the little show sparkled like a tap-tap beat."
        )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    setup_lines(world)
    tension_lines(world)
    resolution_lines(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params = _safe_fact(world, f, "params")
    return [
        f'Write a short rhyming story about {params.hero} and {params.helper} in {world.place.place} where a tiny millimeter gap causes a magical twist.',
        f"Tell a child-friendly magic story that includes teamwork, grace, and the word millimeter, ending with a safe stage and a happy bow.",
        f"Write a rhyming story where two friends fix a small wobble during the first phase of a magic show.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params = _safe_fact(world, f, "params")
    hero, helper, obj = f["hero"], f["helper"], f["obj"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {hero.label} and {helper.label}, who worked together in {world.place.place}.",
        ),
        QAItem(
            question=f"What problem did they have with the {obj.label}?",
            answer=f"The {obj.label} had a {params.gap_mm} millimeter crack, so it could wobble during the magic show.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They used teamwork: {hero.label} held the plank steady and {helper.label} fit in the tiny fix until the stage was safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does millimeter mean?",
            answer="A millimeter is a very tiny unit for measuring length, much smaller than a finger.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together instead of trying alone.",
        ),
        QAItem(
            question="What is a magic trick?",
            answer="A magic trick is a show act that looks surprising and delightful, often with special props and careful practice.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about magic, a twist, teamwork, grace, and millimeters.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=GIRL_NAMES)
    ap.add_argument("--helper", choices=BOY_NAMES)
    ap.add_argument("--object", dest="object", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gap-mm", type=int)
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
    return StoryParams(
        place=getattr(args, "place", None) or rng.choice(list(SETTINGS)),
        hero=getattr(args, "hero", None) or rng.choice(GIRL_NAMES),
        helper=getattr(args, "helper", None) or rng.choice(BOY_NAMES),
        object_id=getattr(args, "object", None) or "stage",
        fix_id=getattr(args, "fix", None) or "shim",
        gap_mm=getattr(args, "gap_mm", None) if getattr(args, "gap_mm", None) is not None else rng.choice([1, 2, 3]),
    )


def asp_facts() -> str:
    import asp

    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("safe_gap_mm", oid, o.safe_gap_mm))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("can_close_mm", fid, f.can_close_mm))
    for gap in [1, 2, 3]:
        lines.append(asp.fact("gap", gap))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(O,G) :- gap(G), safe_gap_mm(O,S), G > S.
compatible(O,F,G) :- at_risk(O,G), can_close_mm(F,C), G <= C.
valid(P,O,F,G) :- affords(P,magic), affords(P,twist), affords(P,teamwork), at_risk(O,G), compatible(O,F,G).
#show valid/4.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n"


def valid_combos() -> list[tuple[str, str, str, int]]:
    combos = []
    for place, p in SETTINGS.items():
        if not {"magic", "twist", "teamwork"}.issubset(p.affords):
            continue
        for oid, o in OBJECTS.items():
            for fid, f in FIXES.items():
                for gap in [1, 2, 3]:
                    if gap > o.safe_gap_mm:
                        if gap <= f.can_close_mm:
                            combos.append((place, oid, fid, gap))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - b:
        print(" only in clingo:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            for gap in [1, 2, 3]:
                params = StoryParams(place=place, hero="Grace", helper="Finn", object_id="stage", fix_id="shim", gap_mm=gap)
                samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
