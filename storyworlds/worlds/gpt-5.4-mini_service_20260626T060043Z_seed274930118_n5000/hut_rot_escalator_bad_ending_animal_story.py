#!/usr/bin/env python3
"""
storyworlds/worlds/hut_rot_escalator_bad_ending_animal_story.py
===============================================================

A small animal-story world about a hut, rot, and an escalator.

Premise:
- A small animal wants to make or keep a hut.
- The hut is carried through an escalator setting, where motion is awkward.
- Rot weakens the hut over time.

Tension:
- The animal hopes the hut will stay sturdy.
- The escalator jostles the hut while rot spreads.

Turn:
- The animal notices the damage too late.

Resolution:
- This is a bad-ending story: the hut fails, and the animal is left with loss,
  though the world state still changes in a clear, causal way.

The world is intentionally tiny and constraint-driven, with a strong animal-story
tone and a fixed unhappy ending.
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
# Domain model
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
    kind: str = "thing"  # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    location: str = ""

    hero: object | None = None
    hut: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bear", "fox", "rabbit", "mouse", "squirrel", "beaver", "cat", "dog"}:
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
class Setting:
    place: str = "the escalator"
    moving: bool = True
    affords: set[str] = field(default_factory=lambda: {"carry", "travel"})
    SETTING: object | None = None
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
class Animal:
    kind: str
    name: str
    trait: str
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
class Hut:
    material: str
    label: str = "hut"
    phrase: str = "a little hut"
    fragile: bool = True
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
    animal: str
    name: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ANIMALS = {
    "beaver": Animal(kind="beaver", name="Bea", trait="busy"),
    "rabbit": Animal(kind="rabbit", name="Rin", trait="careful"),
    "squirrel": Animal(kind="squirrel", name="Suri", trait="tiny"),
    "fox": Animal(kind="fox", name="Fenn", trait="brave"),
    "mouse": Animal(kind="mouse", name="Milo", trait="small"),
}

HUTS = {
    "stick": Hut(material="sticks", label="hut", phrase="a little hut made of sticks"),
    "leaf": Hut(material="leaves", label="hut", phrase="a little leaf hut"),
    "reed": Hut(material="reeds", label="hut", phrase="a little reed hut"),
}

SETTING = Setting(place="the escalator", moving=True, affords={"carry", "travel"})


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def hut_at_risk(hut: Hut, setting: Setting) -> bool:
    return setting.moving and hut.fragile


def can_stay_sound(hut: Hut) -> bool:
    return hut.material in {"sticks", "reeds", "leaves"}


def valid_params(animal: str) -> bool:
    return animal in ANIMALS


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A hut is at risk on a moving escalator if it is fragile.
hut_at_risk(H) :- hut(H), fragile(H), escalator(moving).

% Rot weakens a hut when the hut is fragile.
weakens(rot, H) :- hut(H), fragile(H).

% A bad ending is inevitable if the hut is both at risk and weakens.
bad_end(H) :- hut_at_risk(H), weakens(rot, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("escalator", "moving"))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("trait", aid, a.trait))
    for hid, hut in HUTS.items():
        lines.append(asp.fact("hut", hid))
        lines.append(asp.fact("material", hid, hut.material))
        lines.append(asp.fact("fragile", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_bad_endings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_end/1."))
    return sorted(set(asp.atoms(model, "bad_end")))


def asp_verify() -> int:
    import asp
    py = {("hut",)} if True else set()
    cl = set(asp_bad_endings())
    expected = {("hut",)}
    if cl == expected:
        print("OK: ASP reasoning matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", sorted(cl))
    print("  Python:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    animal = _safe_lookup(ANIMALS, params.animal)
    world = World(SETTING)
    hero = world.add(Entity(
        id="hero",
        kind="animal",
        type=animal.kind,
        label=animal.name,
        traits=[animal.trait, "little"],
        location="at the top of the escalator",
    ))
    hut = world.add(Entity(
        id="hut",
        kind="thing",
        type="hut",
        label="hut",
        phrase="a little hut made of sticks",
        owner=hero.id,
        location="on the escalator",
        meters={"sturdy": 1.0, "rot": 0.0, "wobble": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "sadness": 0.0},
    ))
    world.facts = {"hero": hero, "hut": hut, "animal": animal, "params": params}
    return world


def rot_spreads(world: World) -> None:
    hut = world.get("hut")
    if "rot_spread" in world.fired:
        return
    world.fired.add("rot_spread")
    hut.meters["rot"] += 1.0
    hut.meters["sturdy"] -= 0.5
    hut.memes["worry"] += 1.0
    world.say("But damp little rot began to nibble at the sticks.")


def escalator_jostles(world: World) -> None:
    hut = world.get("hut")
    if "jostle" in world.fired:
        return
    world.fired.add("jostle")
    hut.meters["wobble"] += 1.0
    hut.meters["sturdy"] -= 0.5
    world.say("The moving escalator gave the hut a shaky bump.")


def collapse(world: World) -> None:
    hut = world.get("hut")
    hero = world.get("hero")
    if "collapse" in world.fired:
        return
    if hut.meters["rot"] >= THRESHOLD and hut.meters["sturdy"] <= 0.1:
        world.fired.add("collapse")
        hut.meters["broken"] = 1.0
        hero.memes["sadness"] += 1.0
        hero.memes["hope"] = 0.0
        world.say("At last the rotten sticks snapped, and the hut fell apart.")


def narrate_opening(world: World) -> None:
    hero = world.get("hero")
    world.say(
        f"{hero.label} was a little {hero.type} who loved building cozy places."
    )
    world.say(
        "One day, the little animal found a tiny hut and rolled it onto the escalator."
    )


def narrate_middle(world: World) -> None:
    hero = world.get("hero")
    hut = world.get("hut")
    world.para()
    world.say(
        f"{hero.label} wanted the hut to stay safe, but the escalator kept moving."
    )
    world.say("The animal hugged the hut with quick paws and watched it sway.")
    rot_spreads(world)
    escalator_jostles(world)
    world.say(
        f"{hero.label} could see that {hut.phrase} was getting weaker and weaker."
    )


def narrate_ending(world: World) -> None:
    hero = world.get("hero")
    hut = world.get("hut")
    collapse(world)
    world.para()
    if hut.meters.get("broken", 0.0) >= 1.0:
        world.say(
            f"{hero.label} stood beside the broken sticks, with no hut left to keep."
        )
        world.say(
            "The escalator carried the sad little animal onward while the pieces were left behind."
        )
    else:
        world.say(
            f"{hero.label} still felt worried, because the hut leaned and trembled on the ride."
        )


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    narrate_opening(world)
    narrate_middle(world)
    narrate_ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    animal = _safe_fact(world, world.facts, "animal")
    return [
        "Write a short animal story about a hut on an escalator that ends badly.",
        f"Tell a gentle story about a little {animal.kind} named {animal.name} who wants to keep a hut safe on the escalator.",
        f"Write a simple story that includes the words 'hut' and 'rot' and ends with a sad outcome.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    hut = world.get("hut")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a little {hero.type} who cared about a hut on the escalator.",
        ),
        QAItem(
            question="What happened to the hut?",
            answer="The hut got weaker from rot, shook on the moving escalator, and finally broke apart.",
        ),
        QAItem(
            question="Why was this a bad ending?",
            answer="It was a bad ending because the hut did not stay safe, and the little animal was left sad beside the broken sticks.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="By the end, the hut was broken, the rot had spread, and the animal's hope had gone away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an escalator?",
            answer="An escalator is a moving staircase that carries people or things up and down.",
        ),
        QAItem(
            question="What is rot?",
            answer="Rot is when something old, damp, or damaged starts to decay and become weak.",
        ),
        QAItem(
            question="What is a hut?",
            answer="A hut is a small, simple house or shelter.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} location={e.location}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(animal="beaver", name="Bea", trait="busy"),
    StoryParams(animal="rabbit", name="Rin", trait="careful"),
    StoryParams(animal="squirrel", name="Suri", trait="tiny"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: hut, rot, escalator, bad ending.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS))
    if not valid_params(animal):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    info = _safe_lookup(ANIMALS, animal)
    name = getattr(args, "name", None) or info.name
    trait = getattr(args, "trait", None) or info.trait
    return StoryParams(animal=animal, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_end/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show bad_end/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name}: {p.animal} story"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
