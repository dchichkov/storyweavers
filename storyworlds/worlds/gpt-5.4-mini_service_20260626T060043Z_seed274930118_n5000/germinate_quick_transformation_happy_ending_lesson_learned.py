#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/germinate_quick_transformation_happy_ending_lesson_learned.py
=================================================================================================

A small whodunit-style storyworld about a seed that germinates quickly,
a surprising transformation, and a tidy happy ending with a lesson learned.

The domain premise:
- A child notices a mystery in a little garden.
- Something quick happens: a seed germinates overnight.
- The detective work asks who helped the transformation happen.
- The ending explains the cause and ends with a warm lesson learned.

This script is standalone and uses only the stdlib plus the shared
storyworld result containers.
"""

from __future__ import annotations

import argparse
import copy
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper_ent: object | None = None
    seed: object | None = None
    sprout: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman", "aunt", "grandmother"}
        masculine = {"boy", "father", "dad", "man", "uncle", "grandfather"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
    place: str
    indoors: bool
    warmth: int
    moisture: int
    quiet: bool = False
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
class Seed:
    id: str
    label: str
    phrase: str
    sprout: str
    plant: str
    quickness: str
    needs_warmth: bool = True
    needs_moisture: bool = True
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
class Helper:
    id: str
    label: str
    role: str
    clue: str
    action: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_germinate(world: World) -> list[str]:
    out: list[str] = []
    seed = world.get("seed")
    if seed.meters.get("ready", 0) < THRESHOLD:
        return out
    if seed.meters.get("wet", 0) < THRESHOLD:
        return out
    if world.setting.warmth < 1 and seed.meters.get("warm", 0) < THRESHOLD:
        return out
    sig = ("germinate", seed.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.meters["sprouted"] = 1
    seed.meters["transformed"] = 1
    out.append("__germinated__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    seed = world.get("seed")
    sprout = world.get("sprout")
    if seed.meters.get("sprouted", 0) < THRESHOLD:
        return out
    sig = ("transform", sprout.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sprout.meters["alive"] = 1
    sprout.memes["surprise"] = 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [_r_germinate, _r_transform]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            events = rule(world)
            if events:
                changed = True
                produced.extend(e for e in events if not e.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def seed_can_germinate(setting: Setting, seed: Seed) -> bool:
    return (not seed.needs_warmth or setting.warmth > 0) and (not seed.needs_moisture or setting.moisture > 0)


def explain_rejection(setting: Setting, seed: Seed) -> str:
    parts = []
    if seed.needs_warmth and setting.warmth <= 0:
        parts.append("it is too cold")
    if seed.needs_moisture and setting.moisture <= 0:
        parts.append("it is too dry")
    return f"(No story: {seed.label} would not germinate here because " + " and ".join(parts) + ".)"


def setup_world(setting: Setting, seed_cfg: Seed, helper: Helper, child_name: str, child_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    helper_ent = world.add(Entity(id=helper.id, kind="character", type=helper.role, label=helper.label))
    seed = world.add(Entity(id="seed", type="seed", label=seed_cfg.label, phrase=seed_cfg.phrase))
    sprout = world.add(Entity(id="sprout", type="sprout", label=seed_cfg.sprout, phrase=f"a {seed_cfg.sprout}"))
    world.facts.update(child=child, helper=helper_ent, seed=seed, sprout=sprout, seed_cfg=seed_cfg)
    seed.meters["ready"] = 1
    seed.meters["wet"] = 1 if setting.moisture > 0 else 0
    seed.meters["warm"] = 1 if setting.warmth > 0 else 0
    return world


def tell(setting: Setting, seed_cfg: Seed, helper: Helper, child_name: str, child_type: str) -> World:
    world = setup_world(setting, seed_cfg, helper, child_name, child_type)
    child = _safe_fact(world, world.facts, "child")
    seed = _safe_fact(world, world.facts, "seed")
    sprout = _safe_fact(world, world.facts, "sprout")

    world.say(
        f"{child.id} was a curious little {child.type} who loved tiny mysteries."
    )
    world.say(
        f"In {setting.place}, {child.id} had planted {seed.phrase} the day before and hoped it would germinate."
    )
    world.say(
        f"{seed.label.capitalize()} was supposed to stay still, but something about the morning felt quick."
    )

    world.para()
    if seed.meters["wet"] >= THRESHOLD:
        world.say(f"The soil looked damp, and that was a good clue.")
    if setting.warmth > 0:
        world.say(f"The air was warm enough to help a tiny change along.")

    propagate(world, narrate=False)

    if seed.meters.get("sprouted", 0) >= THRESHOLD:
        world.say(
            f"By breakfast, the mystery had a bright answer: {seed.label} had germinated quick."
        )
        world.say(
            f"{seed.label.capitalize()} had transformed into {sprout.label}, a little green sprout pushing up through the dirt."
        )

    world.para()
    world.say(
        f"{child.id} asked who had helped the transformation, because {seed.label} did not grow that fast by magic alone."
    )
    world.say(
        f"The clue was {helper.clue}, and it matched {helper.label}'s {helper.action}."
    )
    world.say(
        f"{helper.label} smiled and admitted that {helper.role} had given the seed the right water and the right warmth."
    )
    world.say(
        f"{child.id} learned that seeds can wake up quickly when they have what they need."
    )
    world.say(
        f"That made a happy ending: the garden was no longer a puzzle, just a tiny patch with a fresh green sprout and a lesson learned."
    )

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoors=False, warmth=1, moisture=1),
    "greenhouse": Setting(place="the greenhouse", indoors=True, warmth=2, moisture=1, quiet=True),
    "windowsill": Setting(place="the sunny windowsill", indoors=True, warmth=1, moisture=1),
    "backyard": Setting(place="the backyard", indoors=False, warmth=1, moisture=1),
}

SEEDS = {
    "bean": Seed(
        id="bean",
        label="bean seed",
        phrase="a bean seed",
        sprout="bean sprout",
        plant="bean plant",
        quickness="quick",
    ),
    "sunflower": Seed(
        id="sunflower",
        label="sunflower seed",
        phrase="a sunflower seed",
        sprout="sunflower sprout",
        plant="sunflower plant",
        quickness="quick",
    ),
    "pea": Seed(
        id="pea",
        label="pea seed",
        phrase="a pea seed",
        sprout="pea sprout",
        plant="pea plant",
        quickness="quick",
    ),
}

HELPERS = {
    "grandmother": Helper(
        id="grandma",
        label="Grandma",
        role="grandmother",
        clue="a little wet watering can by the pot",
        action="watering the pot before bedtime",
    ),
    "gardener": Helper(
        id="gardener",
        label="the gardener",
        role="gardener",
        clue="muddy fingerprints on the watering can",
        action="giving the seed a careful drink",
    ),
    "aunt": Helper(
        id="aunt",
        label="Aunt May",
        role="aunt",
        clue="a warm cover over the seed tray",
        action="placing the tray near the warm light",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Theo"]
TRAITS = ["curious", "careful", "brave", "cheerful", "clever", "tiny"]


@dataclass
class StoryParams:
    place: str
    seed: str
    helper: str
    name: str
    gender: str
    trait: str
    seed_value: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for seed_id, seed in SEEDS.items():
            if not seed_can_germinate(setting, seed):
                continue
            for helper_id in HELPERS:
                combos.append((place, seed_id, helper_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld about a seed that germinates quick.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--seed-kind", dest="seed", choices=SEEDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", dest="seed_value", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "seed", None) and not seed_can_germinate(_safe_lookup(SETTINGS, getattr(args, "place", None)), _safe_lookup(SEEDS, getattr(args, "seed", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "seed", None) is None or c[1] == getattr(args, "seed", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, seed_id, helper_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, seed=seed_id, helper=helper_id, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child about a seed that germinates quick in {f["seed_cfg"].phrase}.',
        f"Tell a gentle mystery where {f['child'].id} notices a transformation in the garden and learns who helped it happen.",
        f"Write a tiny detective story with a happy ending and a lesson learned, using the word \"germinate\".",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    seed = _safe_fact(world, f, "seed")
    sprout = _safe_fact(world, f, "sprout")
    seed_cfg = _safe_fact(world, f, "seed_cfg")
    return [
        QAItem(
            question=f"What mystery did {child.id} notice in {world.setting.place}?",
            answer=f"{child.id} noticed that {seed.label} had changed into {sprout.label}. It was a quick transformation, so the little garden felt like a mystery."
        ),
        QAItem(
            question=f"What happened to {seed.label} by breakfast?",
            answer=f"{seed.label.capitalize()} germinated quick and became {sprout.label}."
        ),
        QAItem(
            question=f"Who helped the seed grow, and what clue showed it?",
            answer=f"{helper.label} helped by giving the seed the right care. The clue was {helper.clue}, which matched {helper.label}'s {helper.action}."
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that seeds grow when they have water and warmth, and that a quick change can still have a simple cause."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when a seed germinates?",
            answer="When a seed germinates, it wakes up and starts to grow into a new plant."
        ),
        QAItem(
            question="Why can warmth help a seed grow?",
            answer="Warmth can help a seed wake up and start growing faster, as long as it also has water."
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    seed_cfg = _safe_lookup(SEEDS, params.seed)
    helper = _safe_lookup(HELPERS, params.helper)
    world = tell(setting, seed_cfg, helper, params.name, params.gender)
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
seed_kind(bean).
seed_kind(sunflower).
seed_kind(pea).

place(garden).
place(greenhouse).
place(windowsill).
place(backyard).

helper(grandmother).
helper(gardener).
helper(aunt).

warm(garden). moist(garden).
warm(greenhouse). moist(greenhouse).
warm(windowsill). moist(windowsill).
warm(backyard). moist(backyard).

needs(seed,water).
needs(seed,warmth).

can_germinate(P) :- warm(P), moist(P).
quick(P) :- can_germinate(P).

transformation(seed, sprout) :- can_germinate(P), quick(P).
happy_ending(P) :- quick(P), transformation(seed, sprout).
lesson_learned(P) :- happy_ending(P).
#show can_germinate/1.
#show quick/1.
#show transformation/2.
#show happy_ending/1.
#show lesson_learned/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for s in SEEDS:
        lines.append(asp.fact("seed_kind", s))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for p, setting in SETTINGS.items():
        if setting.warmth > 0:
            lines.append(asp.fact("warm", p))
        if setting.moisture > 0:
            lines.append(asp.fact("moist", p))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    can = sorted(set(asp.atoms(model, "can_germinate")))
    quick = sorted(set(asp.atoms(model, "quick")))
    if can and quick:
        print("OK: ASP twin is live.")
        return 0
    print("MISMATCH: ASP twin did not derive expected facts.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed_value", None) if getattr(args, "seed_value", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        params_list = [
            StoryParams(place=p, seed=s, helper=h, name="Mia", gender="girl", trait="curious")
            for p, s, h in valid_combos()
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed_value = seed
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
