#!/usr/bin/env python3
"""
storyworlds/worlds/typical_maximum_transformation_humor_space_adventure.py
===========================================================================

A small space-adventure story world with a gentle transformation mishap and
humorous recovery.

Seed premise:
---
On a typical day aboard a little starship, a kid helper and a friendly robot
go out to fix a flickering antenna. A curious button on the console triggers a
maximum-size transformation beam, turning the helper into something absurdly
large or small. The robot and crew must solve the problem without panicking,
using a clever space-adventure fix.

World shape:
---
- Space setting: ship, moon base, asteroid dock, star garden.
- Transformations: small, huge, floaty, sparkly, and back again.
- Humor comes from mismatched size, awkward movement, and silly but safe fixes.
- The ending proves the helper changed back and the mission succeeded.

This file is standalone and follows the Storyweavers storyworld contract.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    robot: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
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
    place: str
    indoors: bool = False
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
class Gadget:
    id: str
    label: str
    action: str
    effect: str
    kind: str
    transform: str
    fix: str
    safe: str
    speaker: str = "robot"
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


@dataclass
class StoryParams:
    place: str
    gadget: str
    hero_name: str
    hero_type: str
    parent_name: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _apply_transform(world: World) -> None:
    hero = world.get("hero")
    gadget: Gadget = _safe_fact(world, world.facts, "gadget")
    if hero.meters["charge"] < THRESHOLD:
        return
    sig = ("transform", gadget.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters[gadget.kind] += 1
    hero.memes["surprise"] += 1
    if gadget.kind == "huge":
        hero.label = "a giant helper"
    elif gadget.kind == "tiny":
        hero.label = "a tiny helper"
    elif gadget.kind == "floaty":
        hero.label = "a floaty helper"
    elif gadget.kind == "sparkly":
        hero.label = "a sparkly helper"


def _apply_laugh(world: World) -> None:
    hero = world.get("hero")
    robot = world.get("robot")
    if hero.memes["surprise"] >= THRESHOLD and robot.memes["wit"] >= THRESHOLD:
        sig = ("laugh", hero.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        hero.memes["humor"] += 1
        robot.memes["humor"] += 1


def _apply_fix(world: World) -> None:
    hero = world.get("hero")
    gadget: Gadget = _safe_fact(world, world.facts, "gadget")
    if hero.meters["normal"] >= THRESHOLD:
        return
    if world.facts.get("fix_ready") and hero.meters["return"] < THRESHOLD:
        sig = ("fix", hero.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        hero.meters["normal"] += 1
        hero.meters[gadget.kind] = 0
        hero.meters["return"] += 1


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        before = (world.get("hero").meters.get("normal", 0), world.get("hero").meters.get("return", 0))
        _apply_transform(world)
        _apply_laugh(world)
        _apply_fix(world)
        after = (world.get("hero").meters.get("normal", 0), world.get("hero").meters.get("return", 0))
        changed = before != after
    if narrate:
        hero = world.get("hero")
        gadget: Gadget = _safe_fact(world, world.facts, "gadget")
        if hero.meters.get(gadget.kind, 0) >= THRESHOLD:
            if gadget.kind == "huge":
                world.say("A bright beam flashed, and the helper got huge all at once.")
            elif gadget.kind == "tiny":
                world.say("A bright beam flashed, and the helper shrank to a tiny dot.")
            elif gadget.kind == "floaty":
                world.say("A bright beam flashed, and the helper began to bob like a balloon.")
            else:
                world.say("A bright beam flashed, and the helper sparkled like a comet.")
        if hero.memes.get("humor", 0) >= THRESHOLD:
            world.say("The robot made a silly beep, and even the helper had to laugh.")
        if hero.meters.get("normal", 0) >= THRESHOLD:
            world.say("Then the fix worked, and the helper was normal again.")


SETTINGS = {
    "ship": Setting(place="the starship", indoors=True, affords={"antenna", "console"}),
    "moonbase": Setting(place="the moon base", indoors=True, affords={"antenna", "dock"}),
    "dock": Setting(place="the asteroid dock", indoors=False, affords={"dock", "antenna"}),
    "garden": Setting(place="the star garden", indoors=False, affords={"beacon"}),
}

GADGETS = {
    "huge": Gadget(
        id="huge",
        label="the maximum-size ray",
        action="press the maximum-size button",
        effect="grow huge",
        kind="huge",
        transform="huge",
        fix="reverse the size beam",
        safe="size-normalizer",
    ),
    "tiny": Gadget(
        id="tiny",
        label="the tiny-shrink ray",
        action="tap the tiny button",
        effect="shrink tiny",
        kind="tiny",
        transform="tiny",
        fix="reverse the shrink beam",
        safe="size-normalizer",
    ),
    "floaty": Gadget(
        id="floaty",
        label="the floaty-ray",
        action="flip the floaty switch",
        effect="float",
        kind="floaty",
        transform="floaty",
        fix="lower the anti-float field",
        safe="gravity-clip",
    ),
    "sparkly": Gadget(
        id="sparkly",
        label="the sparkle-ray",
        action="push the sparkle button",
        effect="sparkle",
        kind="sparkly",
        transform="sparkly",
        fix="dim the glitter field",
        safe="dust-catcher",
    ),
}

HERO_NAMES = ["Milo", "Nia", "Rae", "Tess", "Juno", "Kai", "Pip", "Zuri"]
ROBOT_NAMES = ["Beep", "Dot", "Zip", "Luma"]
TYPES = ["boy", "girl"]
TRAITS = ["curious", "brave", "cheerful", "bouncy", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for gid in setting.affords:
            if gid in GADGETS:
                out.append((place, gid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure transformation storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--parent")
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "gadget", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "gadget", None) is None or c[1] == getattr(args, "gadget", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, gadget = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(TYPES)
    parent = getattr(args, "parent", None) or rng.choice(["captain", "pilot"])
    return StoryParams(place=place, gadget=gadget, hero_name=name, hero_type=hero_type, parent_name=parent)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    gadget = _safe_lookup(GADGETS, params.gadget)
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    robot = world.add(Entity(id="robot", kind="character", type="thing", label="the robot"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_name, label=params.parent_name))
    robot.memes["wit"] = 1
    hero.meters["normal"] = 1
    hero.meters["charge"] = 0
    hero.meters["return"] = 0
    world.facts["gadget"] = gadget
    world.facts["fix_ready"] = True
    world.say(f"On a typical day at {setting.place}, {hero.label} and the robot checked a flickering space machine.")
    world.say(f"{hero.label.capitalize()} wanted to {gadget.action}, just once, to see what would happen.")
    world.para()
    world.say(f"Then the control panel crackled, and the {gadget.label} fired by mistake.")
    hero.meters["charge"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"The robot and {params.parent_name} hurried in with a {gadget.safe} and a calm plan.")
    if gadget.kind == "huge":
        world.say("They backed away, turned the dial, and let the beam unwind.")
    elif gadget.kind == "tiny":
        world.say("They set out a little ladder, turned the dial, and brought the helper back.")
    elif gadget.kind == "floaty":
        world.say("They clipped on a gravity line, turned the dial, and stopped the wobble.")
    else:
        world.say("They shook loose the glitter field, turned the dial, and dimmed the shine.")
    hero.meters["return"] += 1
    propagate(world, narrate=True)
    world.say(f"By the end, {hero.label} was back to normal, and the crew laughed at the maximum-sized mistake.")
    world.facts.update(hero=hero, robot=robot, parent=parent, setting=setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    g: Gadget = _safe_fact(world, f, "gadget")
    return [
        f'Write a short space-adventure story for a young child about a typical mission that goes wrong because of the {g.label}.',
        f"Tell a humorous story where {f['hero'].label} gets transformed by a {g.transform} beam and the crew fixes it safely.",
        f'Write a child-friendly story with the words "typical" and "maximum" and an ending where the helper is normal again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    gadget: Gadget = _safe_fact(world, f, "gadget")
    return [
        QAItem(
            question=f"What happened to {hero.label} when the {gadget.label} fired?",
            answer=f"{hero.label} got changed by the {gadget.label} and became a {hero.label} for a while before the crew fixed it.",
        ),
        QAItem(
            question=f"Who helped fix the mistake in the story?",
            answer=f"The robot and {parent.label} helped fix the mistake with a calm space plan and the safe gadget.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label}?",
            answer=f"It ended with {hero.label} back to normal, laughing with the crew after the surprising transformation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a starship?",
            answer="A starship is a space vehicle that people use to travel between stars, planets, and space stations.",
        ),
        QAItem(
            question="What does a beam do in a science-fiction story?",
            answer="A beam is a strong line of light or energy that can turn things on, move things, or make surprising changes.",
        ),
        QAItem(
            question="Why can a joke or silly mistake still be safe in a space adventure?",
            answer="It can be safe when the characters stay calm, use careful tools, and fix the problem without hurting anyone.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,G) :- place(Place), gadget(G), affords(Place,G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for g in sorted(s.affords):
            lines.append(asp.fact("affords", place, g))
    for gid in GADGETS:
        lines.append(asp.fact("gadget", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="ship", gadget="huge", hero_name="Milo", hero_type="boy", parent_name="captain"),
    StoryParams(place="moonbase", gadget="tiny", hero_name="Nia", hero_type="girl", parent_name="pilot"),
    StoryParams(place="dock", gadget="floaty", hero_name="Rae", hero_type="girl", parent_name="captain"),
    StoryParams(place="garden", gadget="sparkly", hero_name="Kai", hero_type="boy", parent_name="pilot"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, gadget) combos:\n")
        for place, gadget in combos:
            print(f"  {place:10} {gadget}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.gadget} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
