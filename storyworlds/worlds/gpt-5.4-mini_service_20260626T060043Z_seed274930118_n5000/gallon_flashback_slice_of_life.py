#!/usr/bin/env python3
"""
storyworlds/worlds/gallon_flashback_slice_of_life.py
=====================================================

A small slice-of-life storyworld about a child, a gallon jug, and a gentle
flashback that changes how they handle an ordinary day.

Premise:
- A child wants to carry, pour, or use a gallon jug of something everyday.
- A remembered mishap from an earlier day returns as a flashback.
- The memory nudges the child toward a calmer, safer method.
- The story ends with an ordinary but satisfying result.

This world keeps the action concrete and modest:
- physical state includes carry, spill, weight, and fullness
- emotional state includes eagerness, worry, confidence, relief, and pride

The prose is generated from the simulated world state, not from a frozen template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    jug: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
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
class Container:
    id: str
    label: str
    capacity: float
    spill_risk: float
    acts: set[str]
    phrase: str
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
    action: str
    liquid: str
    container: str
    name: str
    gender: str
    parent: str
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
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "kitchen": Setting("the kitchen", {"pour", "carry", "mix"}),
    "porch": Setting("the porch", {"carry", "pour"}),
    "store": Setting("the small grocery store", {"carry", "buy"}),
    "garden": Setting("the garden", {"carry", "pour", "water"}),
}

LIQUIDS = {
    "milk": "a gallon of milk",
    "lemonade": "a gallon of lemonade",
    "juice": "a gallon of juice",
    "water": "a gallon of water",
}

ACTIONS = {
    "carry": "carry the gallon carefully",
    "pour": "pour from the gallon into a smaller cup",
    "mix": "mix the gallon with something else",
    "water": "water the plants with the gallon",
    "buy": "bring the gallon home",
}

CONTAINERS = {
    "jug": Container("jug", "plastic jug", 4.0, 0.7, {"carry", "pour", "buy"}, "a plastic jug with a twist cap"),
    "pitcher": Container("pitcher", "glass pitcher", 2.0, 0.4, {"pour", "mix"}, "a glass pitcher with a wide mouth"),
    "bottle": Container("bottle", "handled bottle", 1.5, 0.5, {"carry", "buy", "pour"}, "a handled bottle"),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ella", "Ava"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Max", "Sam", "Finn"]
TRAITS = ["curious", "careful", "cheerful", "quiet", "patient", "spirited"]


def safe_combo(place: str, action: str, liquid: str, container: str) -> bool:
    if action not in _safe_lookup(SETTINGS, place).affords:
        return False
    if action not in _safe_lookup(CONTAINERS, container).acts:
        return False
    if liquid == "water" and action == "mix":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in SETTINGS:
        for a in ACTIONS:
            for l in LIQUIDS:
                for c in CONTAINERS:
                    if safe_combo(p, a, l, c):
                        out.append((p, a, l, c))
    return out


def flashback_text(child: Entity, liquid: str, container: Container, action: str) -> str:
    if action == "carry":
        return (
            f"{child.pronoun().capitalize()} remembered a day when the {container.label} slipped "
            f"and a little {liquid} splashed across the floor."
        )
    if action == "pour":
        return (
            f"{child.pronoun().capitalize()} remembered tipping a jug too fast and making a small mess."
        )
    if action == "water":
        return (
            f"{child.pronoun().capitalize()} remembered how heavy a full jug felt in small hands."
        )
    return (
        f"{child.pronoun().capitalize()} remembered how careful hands had saved a spill before."
    )


def _do_action(world: World, child: Entity, container: Entity, action: str) -> None:
    child.meters["busy"] += 1
    if action in {"carry", "buy"}:
        container.meters["held"] += 1
        child.memes["care"] += 1
    elif action == "pour":
        container.meters["empty"] += 1
        child.memes["pride"] += 1
    elif action == "water":
        container.meters["used"] += 1
        child.memes["calm"] += 1
    elif action == "mix":
        child.memes["interest"] += 1


def generate_flashback_and_resolution(world: World, child: Entity, parent: Entity,
                                      liquid: str, action: str, container: Entity) -> None:
    world.say(
        f"On an ordinary afternoon, {child.id} and {child.pronoun('possessive')} {parent.noun()} "
        f"stood near the {world.setting.place.split('the ', 1)[-1]} with {liquid} waiting."
    )
    child.memes["eagerness"] += 1
    world.say(
        f"{child.id} wanted to {_safe_lookup(ACTIONS, action)}."
    )
    world.say(flashback_text(child, liquid, _safe_lookup(CONTAINERS, container.id), action))
    child.memes["worry"] += 1
    if action in {"carry", "buy"}:
        world.say(
            f"So {child.id} put both hands on the {container.label}, kept the cap tight, and walked slowly."
        )
        child.memes["confidence"] += 1
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    elif action == "pour":
        world.say(
            f"So {child.id} held the {container.label} close, poured a little at a time, and watched the stream like a teacher had shown."
        )
        child.memes["confidence"] += 1
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    elif action == "water":
        world.say(
            f"So {child.id} lifted the {container.label} with care, took a breath, and tipped it just enough for the plants."
        )
        child.memes["confidence"] += 1
        child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    else:
        world.say(
            f"So {child.id} mixed only a little at first, just to see the color change."
        )
        child.memes["confidence"] += 1
    _do_action(world, child, container, action)
    world.say(
        f"In the end, the {container.label} stayed steady, the {liquid} did its job, and {child.id} felt proud of the careful choice."
    )


def tell(setting: Setting, action: str, liquid: str, container: Container,
         name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    jug = world.add(Entity(id=container.id, kind="thing", type="container", label=container.label,
                           phrase=container.phrase, owner=child.id))
    world.facts.update(child=child, parent=parent, jug=jug, liquid=liquid, action=action, container=container)
    generate_flashback_and_resolution(world, child, parent, liquid, action, jug)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, action, liquid, container = f["child"], f["action"], f["liquid"], f["container"]
    return [
        f"Write a small slice-of-life story about {child.id} and a {liquid} in a {container.label}.",
        f"Tell a gentle story where a child remembers an earlier spill and then {_safe_lookup(ACTIONS, action)}.",
        f"Write a story that includes a flashback and ends with {child.id} handling the gallon more carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, action, liquid, container = f["child"], f["action"], f["liquid"], f["container"]
    return [
        QAItem(
            question=f"What was {child.id} trying to do with the gallon?",
            answer=f"{child.id} wanted to {_safe_lookup(ACTIONS, action)}."
        ),
        QAItem(
            question=f"What did {child.id} remember from before?",
            answer=(
                f"{child.id} remembered an earlier time when the {container.label} slipped or got handled too fast, "
                f"so the memory made {child.pronoun('object')} more careful."
            )
        ),
        QAItem(
            question=f"How did the story end for the {liquid}?",
            answer=(
                f"The {liquid} stayed useful and the gallon stayed steady because {child.id} used a slower, safer method."
            )
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gallon?",
            answer="A gallon is a large unit for measuring liquid, often used for things like milk or water."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier."
        ),
        QAItem(
            question="Why is it smart to carry a heavy jug with two hands?",
            answer="Using two hands helps keep a heavy jug steady so it is less likely to slip or spill."
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(kitchen). setting(porch). setting(store). setting(garden).
affords(kitchen,carry). affords(kitchen,pour). affords(kitchen,mix).
affords(porch,carry). affords(porch,pour).
affords(store,carry). affords(store,buy).
affords(garden,carry). affords(garden,pour). affords(garden,water).

liquid(milk). liquid(lemonade). liquid(juice). liquid(water).
container(jug). container(pitcher). container(bottle).
acts(jug,carry). acts(jug,pour). acts(jug,buy).
acts(pitcher,pour). acts(pitcher,mix).
acts(bottle,carry). acts(bottle,buy). acts(bottle,pour).

safe(P,A,L,C) :- affords(P,A), acts(C,A), liquid(L), container(C).
#show safe/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for a in _safe_lookup(SETTINGS, p).affords:
            lines.append(asp.fact("affords", p, a))
    for l in LIQUIDS:
        lines.append(asp.fact("liquid", l))
    for c in CONTAINERS.values():
        lines.append(asp.fact("container", c.id))
        for a in c.acts:
            lines.append(asp.fact("acts", c.id, a))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "safe")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "liquid", None) is None or c[2] == getattr(args, "liquid", None))
              and (getattr(args, "container", None) is None or c[3] == getattr(args, "container", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, liquid, container = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, action=action, liquid=liquid, container=container,
                       name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.action, params.liquid, _safe_lookup(CONTAINERS, params.container),
                 params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    StoryParams(place="kitchen", action="pour", liquid="milk", container="jug", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="porch", action="carry", liquid="lemonade", container="bottle", name="Leo", gender="boy", parent="father"),
    StoryParams(place="garden", action="water", liquid="water", container="jug", name="Nora", gender="girl", parent="mother"),
    StoryParams(place="store", action="buy", liquid="juice", container="bottle", name="Ben", gender="boy", parent="father"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a gallon and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--liquid", choices=LIQUIDS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.place} ({p.liquid} in a {p.container})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
