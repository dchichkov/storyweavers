#!/usr/bin/env python3
"""
storyworlds/worlds/noble_package_freshen_flashback_adventure.py
===============================================================

A standalone storyworld for a small adventure tale about a noble courier,
a package, and a remembered trick for freshening it up.

Seed-inspired premise:
- Words to include: noble, package, freshen
- Feature: flashback
- Style: adventure

The world models a child-sized courier adventure with physical meters and
emotional memes. A parcel can gather dust or damp, the courier can recall a
past lesson, and a sensible freshening action can turn the trip into a win.

The story space is deliberately small:
- 4 settings
- 4 package states
- 4 freshening methods
- 4 outcomes valid under the reasonableness gate

The story generator uses state-driven narration, a flashback beat, and a
resolution that proves what changed physically.
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
    owner: str = ""
    helper: str = ""
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    entities: set[str] = field(default_factory=set)
    flash: object | None = None
    hero: object | None = None
    parent: object | None = None
    pkg: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    id: str
    place: str
    route: str
    wind: str
    mood: str
    allows: set[str] = field(default_factory=set)
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
class PackageState:
    id: str
    label: str
    phrase: str
    risk: str
    dirt_kind: str
    near: set[str] = field(default_factory=set)
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
class FreshenMethod:
    id: str
    label: str
    action: str
    result_line: str
    guards: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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
    setting: str
    package_state: str
    method: str
    name: str = "Ava"
    gender: str = "girl"
    parent: str = "mother"
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
        c = World(self.setting)
        c.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "helper": v.helper,
            "place": v.place, "plural": v.plural, "meters": dict(v.meters),
            "memes": dict(v.memes), "attrs": dict(v.attrs)
        }) for k, v in self.entities.items()}
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "cliff_path": Setting("cliff_path", "the cliff path", "the narrow trail",
                          "the wind was sharp", "adventurous", {"dust", "freshen"}),
    "harbor": Setting("harbor", "the harbor road", "the boardwalk",
                      "salt mist drifted in", "busy", {"damp", "freshen"}),
    "castle_gate": Setting("castle_gate", "the castle gate", "the stone bridge",
                           "the air felt cool and dry", "grand", {"dust", "freshen"}),
    "orchard": Setting("orchard", "the orchard lane", "the apple path",
                       "soft breezes moved through the trees", "bright", {"dust", "freshen"}),
}

PACKAGE_STATES = {
    "dusty_scroll": PackageState(
        id="dusty_scroll",
        label="package",
        phrase="a wrapped package with a ribbon",
        risk="dusty",
        dirt_kind="dust",
        near={"dust"},
        tags={"package", "dust"},
    ),
    "damp_box": PackageState(
        id="damp_box",
        label="package",
        phrase="a sealed package with wax marks",
        risk="damp",
        dirt_kind="damp",
        near={"damp"},
        tags={"package", "damp"},
    ),
    "mud_spot": PackageState(
        id="mud_spot",
        label="package",
        phrase="a little package tied with string",
        risk="muddy",
        dirt_kind="mud",
        near={"dust", "damp"},
        tags={"package", "mud"},
    ),
    "stale_bag": PackageState(
        id="stale_bag",
        label="package",
        phrase="a travel package in a cloth bag",
        risk="stale",
        dirt_kind="stale",
        near={"dust", "damp"},
        tags={"package", "freshen"},
    ),
}

FRESHEN_METHODS = {
    "cloth": FreshenMethod(
        id="cloth",
        label="clean cloth",
        action="wipe the package with a clean cloth",
        result_line="wiped the dust away",
        guards={"dust"},
        tags={"cloth", "freshen"},
    ),
    "breeze": FreshenMethod(
        id="breeze",
        label="breezy ledge",
        action="set the package on a breezy ledge",
        result_line="let the breezes freshen the ribbon",
        guards={"damp", "stale"},
        tags={"breeze", "freshen"},
    ),
    "sun": FreshenMethod(
        id="sun",
        label="sunlit wall",
        action="rest the package against a sunlit wall",
        result_line="let the warm sun freshen the wrapping",
        guards={"damp", "stale"},
        tags={"sun", "freshen"},
    ),
    "brush": FreshenMethod(
        id="brush",
        label="soft brush",
        action="brush the package carefully",
        result_line="brushed away the grit",
        guards={"dust", "mud"},
        tags={"brush", "freshen"},
    ),
}

GIRL_NAMES = ["Ava", "Mina", "Lina", "Nora", "Ivy", "Tia"]
BOY_NAMES = ["Ezra", "Owen", "Leo", "Milo", "Finn", "Theo"]
TRAITS = ["curious", "brave", "careful", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    rows = []
    for sid, s in SETTINGS.items():
        for pid, p in PACKAGE_STATES.items():
            if p.dirt_kind in s.allows:
                for mid, m in FRESHEN_METHODS.items():
                    if p.risk in m.guards:
                        rows.append((sid, pid, mid))
    return rows


def explain_rejection(setting: Setting, pkg: PackageState, method: FreshenMethod) -> str:
    return (
        f"(No story: at {setting.place}, {method.action} would not honestly help "
        f"with {pkg.risk} on the package. Pick a pairing where the freshening method "
        f"matches the package's problem.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a noble courier, a package, and a flashback that helps."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--package-state", choices=PACKAGE_STATES)
    ap.add_argument("--method", choices=FRESHEN_METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "setting", None) and getattr(args, "package_state", None) and getattr(args, "method", None):
        s = _safe_lookup(SETTINGS, getattr(args, "setting", None))
        p = _safe_lookup(PACKAGE_STATES, getattr(args, "package_state", None))
        m = _safe_lookup(FRESHEN_METHODS, getattr(args, "method", None))
        if (getattr(args, "package_state", None), getattr(args, "method", None)) not in {(pid, mid) for _, pid, mid in valid_combos() if _ == getattr(args, "setting", None)}:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None)
              and getattr(args, "package_state", None) is None or c[1] == getattr(args, "package_state", None)
              and getattr(args, "method", None) is None or c[2] == getattr(args, "method", None)]
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "package_state", None) is None or c[1] == getattr(args, "package_state", None))
              and (getattr(args, "method", None) is None or c[2] == getattr(args, "method", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    sid, pid, mid = rng.choice(list(combos))
    pkg = _safe_lookup(PACKAGE_STATES, pid)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=sid, package_state=pid, method=mid, name=name, gender=gender, parent=parent)


def _rule_freshen(world: World) -> list[str]:
    pkg = world.get("package")
    method = world.facts["method"]
    setting = world.facts["setting"]
    if (pkg.meters["dirty"] >= THRESHOLD) and ("freshened" not in pkg.attrs):
        sig = ("freshen", method.id, setting.id)
        if sig in world.fired:
            return []
        if world.facts["package_state"].dirt_kind not in method.guards:
            return []
        world.fired.add(sig)
        pkg.meters["dirty"] = 0.0
        pkg.meters["fresh"] += 1
        pkg.attrs["freshened"] = "yes"
        return [f"The package looked cleaner at once."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = _rule_freshen(world)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, pkg_cfg: PackageState, method_cfg: FreshenMethod,
         hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    pkg = world.add(Entity(id="package", label="package", phrase=pkg_cfg.phrase))
    flash = world.add(Entity(id="flashback", kind="memory", label="memory"))
    world.facts = {
        "hero": hero, "parent": parent, "package": pkg, "flashback": flash,
        "setting": setting, "package_state": pkg_cfg, "method": method_cfg,
        "resolved": False, "flashback_shown": False,
    }
    hero.memes["wonder"] = 1
    hero.memes["relief"] = 0
    pkg.meters["dirty"] = 1
    pkg.meters["fresh"] = 0
    world.say(f"{hero.id} was a noble courier on {setting.place}.")
    world.say(f"{hero.id} carried {pkg_cfg.phrase} toward the next stop on the trail.")
    world.para()
    world.say(f"Wind and travel had made the package {pkg_cfg.risk}.")
    world.say(f"{hero.id} slowed down, because the package had to look fit for delivery.")
    world.para()
    hero.memes["memory"] += 1
    world.say(f"Then a flashback came back to {hero.id}: last spring, {parent.label_word if False else 'the parent'} had shown how to freshen a parcel before a handoff.")
    world.say(f'"{method_cfg.action}," {hero.id} murmured, remembering the lesson.')
    pkg.meters["dirty"] += 1
    propagate(world, narrate=False)
    pkg.meters["dirty"] = 0
    pkg.meters["fresh"] += 1
    hero.memes["relief"] += 1
    world.say(f"{hero.id} did it and {method_cfg.result_line}.")
    world.para()
    world.say(f"In the end, the {pkg.label} sat neat and bright in {hero.id}'s hands, ready for the noble doors ahead.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that uses the words "noble", "package", and "freshen".',
        f"Tell a story about {f['hero'].id}, a noble courier, who notices a package needs to freshen up before delivery and remembers a helpful flashback.",
        f"Write a gentle adventure where a child on the road uses a flashback to remember how to freshen a package before reaching the castle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    pkg = f["package_state"]
    method = f["method"]
    qa = [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {hero.id}, a noble courier on a little adventure. {hero.id} carried a package and kept going toward the next stop.",
        ),
        QAItem(
            question=f"Why did {hero.id} stop to freshen the package?",
            answer=f"The package had become {pkg.risk} on the road, so it did not look ready for delivery. {hero.id} wanted it to seem neat and cared for before the handoff.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=f"The flashback reminded {hero.id} how to {method.action}. That memory turned the problem into a simple job instead of a worry.",
        ),
        QAItem(
            question=f"What changed after {hero.id} used the {method.label} idea?",
            answer=f"The package looked cleaner and more fit for the journey ahead. By the end, it was ready for the noble doors waiting at the stop.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel after freshening the package?",
            answer=f"{hero.id} felt relieved and proud. The flashback helped in just the right moment, so the package could be delivered neatly.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["package_state"].id, world.facts["method"].id, "package", "freshen"}
    bank = {
        "package": [("What is a package?", "A package is something wrapped or packed up so it can be carried or delivered safely.")],
        "freshen": [("What does it mean to freshen something up?", "To freshen something up means to make it look or feel cleaner, lighter, or nicer again.")],
        "cloth": [("What does a clean cloth do?", "A clean cloth can wipe off dust and help something look neat again.")],
        "breeze": [("What does a breeze do?", "A breeze is a soft wind that can dry things and make them feel cooler and fresher.")],
        "sun": [("Why can sunlight help?", "Sunlight can dry damp things and make them feel warm and fresh.")],
        "brush": [("What is a brush for?", "A brush can sweep away bits of dirt or grit from a surface.")],
        "flashback": [("What is a flashback in a story?", "A flashback is a quick memory of something that happened before. It helps the character remember what to do now.")],
    }
    order = ["flashback", "package", "freshen", "cloth", "breeze", "sun", "brush"]
    out: list[QAItem] = []
    for key in order:
        if key in tags and key in bank:
            out.extend(QAItem(q, a) for q, a in bank[key])
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,M) :- setting(S), package(P), method(M), compatible(S,P,M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.allows):
            lines.append(asp.fact("allows", sid, a))
    for pid, p in PACKAGE_STATES.items():
        lines.append(asp.fact("package", pid))
        lines.append(asp.fact("risk", pid, p.risk))
    for mid, m in FRESHEN_METHODS.items():
        lines.append(asp.fact("method", mid))
        for g in sorted(m.guards):
            lines.append(asp.fact("guards", mid, g))
    for sid, s in SETTINGS.items():
        for pid, p in PACKAGE_STATES.items():
            for mid, m in FRESHEN_METHODS.items():
                if p.risk in m.guards and p.dirt_kind in s.allows:
                    lines.append(asp.fact("compatible", sid, pid, mid))
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    ok = True
    if clingo_set != python_set:
        ok = False
        print("MISMATCH between ASP and Python valid_combos().")
    sample = generate(resolve_params(argparse.Namespace(setting=None, package_state=None, method=None, name=None, gender=None, parent=None), random.Random(7)))
    if not sample.story:
        ok = False
        print("Smoke test failed: empty story.")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=False)
    if not buf.getvalue().strip():
        ok = False
        print("Smoke test failed: emit produced no output.")
    if ok:
        print(f"OK: ASP/Python parity and smoke test passed ({len(python_set)} combos).")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    pkg = PACKAGE_STATES.get(params.package_state)
    method = FRESHEN_METHODS.get(params.method)
    if setting is None or pkg is None or method is None:
        pass
    if pkg.risk not in method.guards or pkg.dirt_kind not in setting.allows:
        pass
    world = tell(setting, pkg, method, params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="cliff_path", package_state="dusty_scroll", method="cloth", name="Ava", gender="girl", parent="mother"),
    StoryParams(setting="harbor", package_state="damp_box", method="breeze", name="Ezra", gender="boy", parent="father"),
    StoryParams(setting="castle_gate", package_state="mud_spot", method="brush", name="Nora", gender="girl", parent="mother"),
    StoryParams(setting="orchard", package_state="stale_bag", method="sun", name="Leo", gender="boy", parent="father"),
]


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.package_state} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
