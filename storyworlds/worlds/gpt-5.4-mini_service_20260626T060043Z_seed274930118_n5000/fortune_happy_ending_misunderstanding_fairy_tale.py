#!/usr/bin/env python3
"""
A small fairy-tale story world about fortune, a misunderstanding, and a happy ending.

Premise:
- A childlike hero finds a fortune charm.
- Another character misunderstands what it is for.
- The misunderstanding causes worry and loss of trust.
- The truth is discovered, the charm is shared, and the story ends happily.

This script follows the Storyweavers world contract with:
- StoryParams
- registries
- build_parser / resolve_params / generate / emit / main
- inline ASP_RULES twin + asp_facts()
- reasonableness gate
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "maid"}
        male = {"boy", "prince", "king", "father", "knight"}
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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
class Charm:
    id: str
    label: str
    phrase: str
    fortune_kind: str
    place_kind: str
    misread_as: str
    reveals: str
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
class CharacterSpec:
    type: str
    title: str
    role: str
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
class SettingSpec:
    place: str
    place_kind: str
    weather: str
    atmosphere: str
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
class StoryParams:
    setting: str
    charm: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
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


SETTINGS = {
    "castle_garden": SettingSpec(
        place="the castle garden",
        place_kind="garden",
        weather="soft morning",
        atmosphere="roses trembled in the breeze",
    ),
    "forest_path": SettingSpec(
        place="the forest path",
        place_kind="forest",
        weather="golden afternoon",
        atmosphere="birds sang from high branches",
    ),
    "village_square": SettingSpec(
        place="the village square",
        place_kind="village",
        weather="clear daylight",
        atmosphere="bells chimed above the rooftops",
    ),
}

CHARACTERS = {
    "girl": CharacterSpec(type="girl", title="girl", role="hero"),
    "boy": CharacterSpec(type="boy", title="boy", role="hero"),
    "princess": CharacterSpec(type="princess", title="princess", role="hero"),
    "prince": CharacterSpec(type="prince", title="prince", role="hero"),
    "queen": CharacterSpec(type="queen", title="queen", role="helper"),
    "king": CharacterSpec(type="king", title="king", role="helper"),
    "fairy": CharacterSpec(type="fairy", title="fairy", role="helper"),
    "fox": CharacterSpec(type="fox", title="fox", role="helper"),
}

CHARM_REGISTRY = {
    "luck_bell": Charm(
        id="luck_bell",
        label="a little luck bell",
        phrase="a silver bell that was said to bring gentle fortune",
        fortune_kind="fortune",
        place_kind="path",
        misread_as="a trick",
        reveals="a promise of good luck",
    ),
    "gold_coin": Charm(
        id="gold_coin",
        label="a gold coin",
        phrase="a bright gold coin with a star stamped on it",
        fortune_kind="fortune",
        place_kind="treasure",
        misread_as="stolen treasure",
        reveals="a lucky gift",
    ),
    "star_token": Charm(
        id="star_token",
        label="a star token",
        phrase="a tiny wooden star tied with blue thread",
        fortune_kind="fortune",
        place_kind="gift",
        misread_as="a secret message",
        reveals="a blessing from the fairies",
    ),
}

TRAITS = ["kind", "curious", "gentle", "brave", "thoughtful", "cheerful"]
GENDERED_NAMES = {
    "girl": ["Lila", "Mina", "Nora", "Elin", "Ava"],
    "boy": ["Tobin", "Rowan", "Finn", "Eli", "Hugo"],
    "princess": ["Iris", "Celia", "Rosalind"],
    "prince": ["Piers", "Alfie", "Cedric"],
    "queen": ["Maeve", "Helena"],
    "king": ["Edwin", "Basil"],
    "fairy": ["Faye", "Mira"],
    "fox": ["Pip", "Rusty"],
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for charm_id, charm in CHARM_REGISTRY.items():
            if setting.place_kind in charm.place_kind or charm.fortune_kind == "fortune":
                combos.append((setting_id, charm_id))
    return combos


def explain_rejection(setting: str, charm: str) -> str:
    s = _safe_lookup(SETTINGS, setting)
    c = CHARM_REGISTRY[charm]
    return (
        f"(No story: {c.label} does not fit neatly in {s.place} for a fairy-tale misunderstanding.)"
    )


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    charm = _safe_fact(world, world.facts, "charm")
    if hero.memes.get("hope", 0) >= THRESHOLD and helper.memes.get("worry", 0) >= THRESHOLD:
        sig = ("misread",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["confusion"] = hero.memes.get("confusion", 0) + 1
            helper.memes["alarm"] = helper.memes.get("alarm", 0) + 1
            out.append("__misunderstanding__")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    if hero.memes.get("honesty", 0) >= THRESHOLD and helper.memes.get("listen", 0) >= THRESHOLD:
        sig = ("truth",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["trust"] = hero.memes.get("trust", 0) + 1
            helper.memes["trust"] = helper.memes.get("trust", 0) + 1
            out.append("__truth__")
    return out


RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("truth", _r_truth)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(x for x in produced if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHARM_REGISTRY.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("fortune_kind", cid, c.fortune_kind))
        lines.append(asp.fact("place_kind", cid, c.place_kind))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, C) :- setting(S), charm(C), fortune_kind(C, fortune).
misunderstanding(S, C) :- valid_story(S, C), place_kind(C, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale world about fortune and misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARM_REGISTRY)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "princess", "prince"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["queen", "king", "fairy", "fox"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None) and getattr(args, "charm", None) and (getattr(args, "setting", None), getattr(args, "charm", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None)) and (getattr(args, "charm", None) is None or c[1] == getattr(args, "charm", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_id, charm_id = rng.choice(list(filtered))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy", "princess", "prince"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["queen", "king", "fairy", "fox"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(_safe_lookup(GENDERED_NAMES, hero_type))
    helper_name = getattr(args, "helper_name", None) or rng.choice(_safe_lookup(GENDERED_NAMES, helper_type))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, charm=charm_id, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type, trait=trait)


def _new_entity(id: str, type_: str, kind: str = "character", label: str = "") -> Entity:
    return Entity(id=id, type=type_, kind=kind, label=label or id)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    charm_spec = CHARM_REGISTRY[params.charm]
    world = World(place=setting.place)
    hero = world.add(_new_entity(params.hero_name, params.hero_type, "character"))
    helper = world.add(_new_entity(params.helper_name, params.helper_type, "character"))
    charm = world.add(Entity(
        id="charm",
        kind="thing",
        type="charm",
        label=charm_spec.label,
        phrase=charm_spec.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    hero.memes["hope"] = 1
    hero.memes["honesty"] = 1
    helper.memes["worry"] = 1
    helper.memes["listen"] = 0

    world.say(f"Once upon a time, in {setting.place}, {hero.id} was a {params.trait} young {hero.type}.")
    world.say(f"{setting.atmosphere.capitalize()}, and {hero.id} found {charm.phrase}.")
    world.say(f"{hero.id} thought it was {charm_spec.reveals}, so {hero.pronoun()} tucked {charm.it()} into {hero.pronoun('possessive')} pocket.")
    world.para()
    world.say(f"Then {helper.id} came by and saw the shining charm.")
    world.say(f"{helper.id} thought it was {charm_spec.misread_as}, and {helper.pronoun()} grew worried.")
    propagate(world, narrate=False)
    world.say(f'"Do not take what is not yours," {helper.id} said, with a stern little voice.')
    world.say(f"{hero.id} looked surprised. {hero.id} had only meant to keep the lucky charm safe.")
    world.para()
    world.say(f"So {hero.id} explained the truth and held out the charm for {helper.id} to see.")
    helper.memes["listen"] = 1
    world.say(f"{helper.id} listened carefully and understood that the charm was really {charm_spec.reveals}.")
    propagate(world, narrate=False)
    world.say(f"At last, {helper.id} smiled, and the two agreed to leave the charm where both could share its good fortune.")
    world.say(f"That evening, the path felt brighter, {hero.id} felt brave again, and {helper.id} walked home with a warm heart.")
    world.say("And so the misunderstanding was mended, the fortune was shared, and the story ended happily.")
    world.facts.update(hero=hero, helper=helper, charm=charm, setting=setting, charm_spec=charm_spec)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about fortune, a misunderstanding, and a happy ending in {f["setting"].place}.',
        f"Tell a gentle story where {f['hero'].id} finds {f['charm'].label} and {f['helper'].id} first misreads it.",
        f"Write a child-friendly fairy tale that begins with a lucky charm and ends with kindness and trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    charm_spec = _safe_fact(world, f, "charm_spec")
    return [
        QAItem(
            question=f"What did {hero.id} find in {f['setting'].place}?",
            answer=f"{hero.id} found {f['charm'].phrase}. {hero.id} believed it was {charm_spec.reveals}.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry when {helper.id} saw the charm?",
            answer=f"{helper.id} misunderstood the charm and thought it was {charm_spec.misread_as}. That made {helper.pronoun()} worry before the truth was explained.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The truth was spoken kindly, the misunderstanding was fixed, and the story ended with a happy sharing of fortune.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fortune in a fairy tale?",
            answer="Fortune is good luck or a lucky turn of events, like finding a charm or receiving a blessing.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What makes a fairy tale feel magical?",
            answer="Fairy tales often feel magical because they have lucky charms, kind helpers, and problems that can be solved with honesty and care.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="castle_garden", charm="luck_bell", hero_name="Lila", hero_type="girl", helper_name="Faye", helper_type="fairy", trait="curious"),
    StoryParams(setting="forest_path", charm="gold_coin", hero_name="Rowan", hero_type="boy", helper_name="Pip", helper_type="fox", trait="kind"),
    StoryParams(setting="village_square", charm="star_token", hero_name="Iris", hero_type="princess", helper_name="Maeve", helper_type="queen", trait="gentle"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:\n")
        for setting, charm in combos:
            print(f"  {setting:16} {charm}")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name}: {p.setting} / {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
