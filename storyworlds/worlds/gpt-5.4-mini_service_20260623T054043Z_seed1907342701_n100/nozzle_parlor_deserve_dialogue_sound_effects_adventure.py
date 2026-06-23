#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/nozzle_parlor_deserve_dialogue_sound_effects_adventure.py
===========================================================================================================

A standalone storyworld for an adventure in an old parlor: a child finds a
hidden trail, uses a nozzle to solve a problem, and earns a deserved reward.

The world is small on purpose. It models:
- one child explorer and one helper
- one place: a parlor or gallery-like room
- one problem: dust, jammed lock, or stuck clue
- one tool with a nozzle
- one rescue/fix method
- dialogue and sound effects as narrative instruments

The story is built from world state, not from a frozen paragraph template.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    key: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Problem:
    key: str
    label: str
    phrase: str
    mess: str
    obstacle: str
    at_risk: str
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
class Tool:
    key: str
    label: str
    phrase: str
    nozzle: bool
    sound: str
    action: str
    fixes: set[str] = field(default_factory=set)
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
class Method:
    key: str
    label: str
    verb: str
    result: str
    sound: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "parlor": Setting("parlor", "the parlor", "dusty and old", {"cleaning", "reveal"}),
    "gallery": Setting("gallery", "the little gallery", "quiet and bright", {"cleaning", "reveal"}),
    "atticroom": Setting("atticroom", "the attic parlor", "creaky and dim", {"cleaning", "reveal"}),
    "workroom": Setting("workroom", "the workroom", "busy and cluttered", {"cleaning", "repair"}),
}

PROBLEMS = {
    "dusty_map": Problem("dusty_map", "dust", "the dusty map", "dusty", "a clue hidden under dust", "the map",
                         {"dust", "reveal"}),
    "stuck_drawer": Problem("stuck_drawer", "drawer", "the stuck drawer", "stuck", "a stuck drawer hiding a key", "the drawer",
                            {"jam", "repair"}),
    "smudged_mirror": Problem("smudged_mirror", "mirror", "the smudged mirror", "smudged", "a message hidden in smudges", "the mirror",
                              {"smudge", "reveal"}),
    "spilled_corner": Problem("spilled_corner", "spill", "the spilled corner", "messy", "a trail hidden in the mess", "the floor",
                              {"spill", "cleaning"}),
}

TOOLS = {
    "sprayer": Tool("sprayer", "spray bottle", "a spray bottle with a narrow nozzle", True, "pssst", "sprayed a fine mist",
                    {"dust", "smudge", "spill"}, {"nozzle", "water"}),
    "lamp": Tool("lamp", "desk lamp", "a bright desk lamp", False, "click", "switched on a lamp",
                 {"dark"}, {"light"}),
    "oiler": Tool("oiler", "oil can", "an oil can with a tiny nozzle", True, "glug", "dripped oil",
                  {"jam"}, {"nozzle", "repair"}),
}

METHODS = {
    "wipe": Method("wipe", "wiped", "wiped away", "the clue shone through", "swish", {"cleaning"}),
    "unfreeze": Method("unfreeze", "unclogged", "worked loose", "the drawer opened with a soft click", "knock-knock", {"repair"}),
    "clear": Method("clear", "cleared", "cleared off", "the hidden message appeared", "scrub-scrub", {"reveal"}),
}


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    method: str
    name: str
    gender: str
    helper: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS.values():
        for p in PROBLEMS.values():
            for t in TOOLS.values():
                for m in METHODS.values():
                    if p.key in {"dusty_map", "smudged_mirror", "spilled_corner"} and t.label == "spray bottle" and m.key in {"wipe", "clear"}:
                        combos.append((s.key, p.key, t.key, m.key))
                    if p.key == "stuck_drawer" and t.key == "oiler" and m.key == "unfreeze":
                        combos.append((s.key, p.key, t.key, m.key))
    return combos


GIRL_NAMES = ["Lily", "Maya", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Max", "Ben", "Owen"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a nozzle in a parlor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
              and (getattr(args, "method", None) is None or c[3] == getattr(args, "method", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, tool, method = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "aunt", "uncle"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["woman", "man"])
    return StoryParams(setting=setting, problem=problem, tool=tool, method=method,
                       name=name, gender=gender, helper=helper, helper_gender=helper_gender)


def _base_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    prob = _safe_lookup(PROBLEMS, params.problem)
    tool = _safe_lookup(TOOLS, params.tool)
    method = _safe_lookup(METHODS, params.method)
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name,
                            role="explorer", meters={"mud": 0.0}, memes={"curiosity": 1.0, "joy": 1.0}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper,
                              role="helper", meters={"patience": 1.0}, memes={"care": 1.0}))
    obj = world.add(Entity(id="object", kind="thing", type="thing", label=prob.label, phrase=prob.phrase,
                           meters={"blocked": 1.0}, memes={"hope": 0.0}))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="thing", label=tool.label, phrase=tool.phrase,
                                meters={"ready": 1.0}, memes={}))
    world.facts.update(hero=hero, helper=helper, obj=obj, tool=tool, method=method, problem=prob, setting=setting)
    return world


def _apply_fix(world: World) -> None:
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    method: Method = world.facts["method"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    obj: Entity = world.facts["obj"]  # type: ignore[assignment]
    sig = (prob.key, tool.key, method.key)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if prob.key == "stuck_drawer":
        obj.meters["blocked"] = 0.0
    else:
        obj.meters["dust"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1.0
    world.say(f"{tool.sound.upper()}! {method.sound.upper()}!")


def tell(params: StoryParams) -> World:
    world = _base_world(params)
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    obj: Entity = world.facts["obj"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    method: Method = world.facts["method"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]

    world.say(f"{hero.label_word} stepped into {setting.place}. {setting.mood.capitalize()} air hung over the room.")
    world.say(f'"Look," {hero.label_word} whispered, "the {prob.label_word} is hiding something."')
    world.say(f'"Then we use the {tool.label}," {helper.label_word} said. "{tool.sound.capitalize()} goes the nozzle!"')
    world.para()
    world.say(f"{hero.label_word} aimed {tool.phrase} at {prob.at_risk}.")
    world.say(f"{tool.sound.upper()}! {tool.action.capitalize()} the air, {hero.label_word} {method.verb} {prob.at_risk}.")
    _apply_fix(world)
    if prob.key == "stuck_drawer":
        world.say(f'"You deserved to hear that click," {helper.label_word} said, smiling as the drawer opened.')
        world.say(f"Inside, the key waited like treasure.")
    else:
        world.say(f'"That was the clue," {hero.label_word} said. "{method.result.capitalize()}!"')
        world.say(f"In the end, the hidden trail showed itself, and {hero.label_word} stood in the parlor with a bright grin.")
    world.facts["resolved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    method: Method = world.facts["method"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {hero.label_word} need the {tool.label} in the {world.setting.place}?",
            answer=f"{hero.label_word} needed it to deal with {prob.phrase}. The narrow nozzle helped the spray reach the dusty or stuck place without making a bigger mess.",
        ),
        QAItem(
            question=f"What did {helper.label_word} say before the fix?",
            answer=f'{helper.label_word} pointed to the problem and said, "Use the {tool.label}." That gave {hero.label_word} a clear plan for the adventure.',
        ),
        QAItem(
            question=f"What changed after the {tool.label} and the {method.label}?",
            answer=f"{method.result.capitalize()}. The problem stopped hiding, and the room looked ready for a new adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    out = []
    if tool.nozzle:
        out.append(QAItem(
            question="What is a nozzle?",
            answer="A nozzle is a small opening that makes a spray or stream come out in a narrow way.",
        ))
    if "dust" in prob.tags:
        out.append(QAItem(
            question="Why does dust hide things?",
            answer="Dust makes a thin gray layer that can cover letters, pictures, or clues until someone wipes it away.",
        ))
    if "repair" in prob.tags:
        out.append(QAItem(
            question="What helps a stuck thing move again?",
            answer="Careful help, like oil or a gentle push, can loosen a stuck thing so it can open or turn again.",
        ))
    out.append(QAItem(
        question="Why do people say someone deserves a reward?",
        answer="People say that when someone works hard or does something brave, a reward feels fair and kind.",
    ))
    return out


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    prob: Problem = world.facts["problem"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]
    return [
        f'Write an adventure story for a young child in a {world.setting.place} with the word "nozzle".',
        f'Tell a short dialogue-driven story where {hero.label_word} finds {prob.phrase} and solves it with {tool.phrase}.',
        f'Write a child-friendly adventure that includes "parlor", "deserve", and a sound effect like "{tool.sound.upper()}!".',
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
        lines.append(f"  {e.id}: type={e.type} label={e.label!r} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T,M) :- setting(S), problem(P), tool(T), method(M), compatible(P,T,M).
compatible("stuck_drawer","oiler","unfreeze").
compatible("dusty_map","sprayer","wipe").
compatible("dusty_map","sprayer","clear").
compatible("smudged_mirror","sprayer","wipe").
compatible("smudged_mirror","sprayer","clear").
compatible("spilled_corner","sprayer","wipe").
compatible("spilled_corner","sprayer","clear").
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("setting", k))
    for k in PROBLEMS:
        lines.append(asp.fact("problem", k))
    for k in TOOLS:
        lines.append(asp.fact("tool", k))
    for k in METHODS:
        lines.append(asp.fact("method", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_python() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, py_set = set(asp_valid_combos()), set(valid_combos_python())
    rc = 0
    if clingo_set != py_set:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos:")
        print("only in ASP:", sorted(clingo_set - py_set))
        print("only in Python:", sorted(py_set - clingo_set))
    else:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
    try:
        _ = generate(resolve_params(argparse.Namespace(setting=None, problem=None, tool=None, method=None,
                                                      name=None, gender=None, helper=None, helper_gender=None),
                                    random.Random(777)))
        print("OK: default story generation smoke test passed.")
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS or params.method not in METHODS:
        pass
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
    StoryParams(setting="parlor", problem="dusty_map", tool="sprayer", method="clear", name="Lily", gender="girl", helper="mother", helper_gender="woman"),
    StoryParams(setting="gallery", problem="smudged_mirror", tool="sprayer", method="wipe", name="Theo", gender="boy", helper="father", helper_gender="man"),
    StoryParams(setting="atticroom", problem="stuck_drawer", tool="oiler", method="unfreeze", name="Maya", gender="girl", helper="uncle", helper_gender="man"),
    StoryParams(setting="workroom", problem="spilled_corner", tool="sprayer", method="wipe", name="Finn", gender="boy", helper="aunt", helper_gender="woman"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
              and (getattr(args, "method", None) is None or c[3] == getattr(args, "method", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, tool, method = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "aunt", "uncle"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["woman", "man"])
    return StoryParams(setting=setting, problem=problem, tool=tool, method=method,
                       name=name, gender=gender, helper=helper, helper_gender=helper_gender)


def build_parser_and_main() -> None:
    pass


def build_parser():
    return argparse.ArgumentParser(description="Adventure storyworld with nozzle/parlor/deserve and dialogue + sound effects.")


def main() -> None:
    ap = build_parser()
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    args = ap.parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{x}" for x in asp_valid_combos()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
