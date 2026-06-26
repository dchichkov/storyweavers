#!/usr/bin/env python3
"""
A standalone storyworld for a small Detective Story domain with a tempest,
papered clues, and inner monologue.

The tale premise:
A careful child detective notices that a papered map has gone missing during a
tempest. The detective follows clues, thinks through suspects in inner
monologue, and discovers that the "theft" was actually a rescue from the rain.

The world is small and constraint-checked:
- a place may or may not be storm-safe
- a papered clue can be damaged by water
- a weatherproof folder or tin can protect papered evidence
- the detective's inner monologue is only narrated when it meaningfully changes
  the reasoning or the final reveal

This file is self-contained except for the shared result containers in
storyworlds/results.py and the lazy ASP helper in storyworlds/asp.py.
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
    carried_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    hero: object | None = None
    partner: object | None = None
    protected: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the old museum"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)
    storm_safe: bool = False
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
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    papered: bool = False
    region: str = "hands"
    requires_dry: bool = False
    danger: str = "wet"
    tags: set[str] = field(default_factory=set)
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
class Protection:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""
        self.storm_active: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.weather = self.weather
        clone.storm_active = self.storm_active
        return clone

    def worn_or_carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id or e.carried_by == actor.id]


def _r_wet_paper(world: World) -> list[str]:
    out: list[str] = []
    if not world.storm_active:
        return out
    for clue in list(world.entities.values()):
        if clue.type != "clue" or not clue.papered:
            continue
        if clue.meters.get("dry", 0.0) >= THRESHOLD:
            continue
        carrier = clue.carried_by
        if not carrier:
            continue
        sig = ("wet_paper", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if not any(
            item.protective and ("paper" in item.guards or "water" in item.guards)
            for item in world.worn_or_carried_items(world.get(carrier))
        ):
            clue.meters["damaged"] = clue.meters.get("damaged", 0.0) + 1
            out.append(f"The papered clue would have gone limp in the tempest.")
    return out


def _r_attention(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    if detective is None:
        return out
    if detective.memes.get("suspicion", 0.0) < THRESHOLD:
        return out
    sig = ("attention", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["focus"] = detective.memes.get("focus", 0.0) + 1
    out.append("__focus__")
    return out


def _r_resolution(world: World) -> list[str]:
    out: list[str] = []
    detective = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    if detective is None:
        return out
    if detective.memes.get("focus", 0.0) < THRESHOLD:
        return out
    if detective.memes.get("relief", 0.0) >= THRESHOLD:
        return out
    sig = ("resolution", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
    out.append("__resolution__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_wet_paper, _r_attention, _r_resolution):
            parts = rule(world)
            if parts:
                changed = True
                produced.extend(p for p in parts if not p.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def make_setting() -> Setting:
    return Setting(place="the old museum", indoor=True, affords={"search", "inspect", "follow"}, storm_safe=True)


SETTINGS = {
    "museum": Setting(place="the old museum", indoor=True, affords={"search", "inspect", "follow"}, storm_safe=True),
    "library": Setting(place="the dim library", indoor=True, affords={"search", "inspect", "follow"}, storm_safe=True),
    "dock": Setting(place="the rain-battered dock office", indoor=False, affords={"search", "inspect", "follow"}, storm_safe=False),
}


CLUES = {
    "map": Clue(
        id="map",
        label="map",
        phrase="a folded paper map with a blue pencil line",
        location="desk drawer",
        papered=True,
        region="hands",
        requires_dry=True,
        danger="wet",
        tags={"papered", "map", "paper"},
    ),
    "note": Clue(
        id="note",
        label="note",
        phrase="a papered note with one corner taped flat",
        location="coat pocket",
        papered=True,
        region="hands",
        requires_dry=True,
        danger="wet",
        tags={"papered", "note", "paper"},
    ),
    "receipt": Clue(
        id="receipt",
        label="receipt",
        phrase="a paper receipt with a messy stamp",
        location="counter tray",
        papered=True,
        region="hands",
        requires_dry=True,
        danger="wet",
        tags={"papered", "receipt", "paper"},
    ),
}

PROTECTIONS = [
    Protection(
        id="folder",
        label="a waxed folder",
        phrase="a waxed folder",
        guards={"water", "paper"},
        covers={"hands"},
        prep="slide the clue into a waxed folder",
        tail="kept the papered clue dry in the storm",
    ),
    Protection(
        id="tin",
        label="a little tin case",
        phrase="a little tin case",
        guards={"water", "paper"},
        covers={"hands"},
        prep="hide the clue inside a little tin case",
        tail="carried the clue safely through the tempest",
        plural=False,
    ),
]

NAMES = ["Mina", "Noah", "Iris", "Leo", "Ada", "Eli", "Maya", "Finn"]
TRAITS = ["careful", "quiet", "sharp-eyed", "patient", "brave"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    name: str
    gender: str
    trait: str
    tempested: bool = True
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


def clue_at_risk(clue: Clue, setting: Setting) -> bool:
    return clue.papered and not setting.storm_safe


def select_protection(clue: Clue, setting: Setting) -> Optional[Protection]:
    if not clue_at_risk(clue, setting):
        return None
    return _safe_lookup(PROTECTIONS, 0) if clue.papered else None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world with a tempest and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s_id, s in SETTINGS.items():
        for c_id, c in CLUES.items():
            if clue_at_risk(c, s) and select_protection(c, s):
                combos.append((s_id, c_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "clue", None):
        if not clue_at_risk(_safe_lookup(CLUES, getattr(args, "clue", None)), _safe_lookup(SETTINGS, getattr(args, "setting", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, clue = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, name=name, gender=gender, trait=trait)


def _hero_pronouns(gender: str) -> dict[str, str]:
    return {
        "subject": "she" if gender == "girl" else "he",
        "object": "her" if gender == "girl" else "him",
        "possessive": "her" if gender == "girl" else "his",
    }


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    clue_cfg = _safe_lookup(CLUES, params.clue)
    world = World(setting)
    world.weather = "tempest"
    world.storm_active = True

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"suspicion": 0.0, "focus": 0.0}))
    partner = world.add(Entity(id="Partner", kind="character", type="mother" if params.gender == "girl" else "father", label="the partner"))
    clue = world.add(Entity(
        id=clue_cfg.id,
        kind="thing",
        type="clue",
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        owner=hero.id,
        caretaker=partner.id,
        carried_by=hero.id,
        protective=False,
        meters={"dry": 1.0},
    ))

    hero_p = _hero_pronouns(params.gender)

    world.say(f"{params.name} was a {params.trait} little detective who noticed every scuff and whisper in {setting.place}.")
    world.say(f"{hero_p['subject'].capitalize()} liked to think in short, careful lines: what moved, what hid, and what did not belong.")
    world.say(f"One evening, {params.name} found {clue.phrase} and kept {clue.it()} close, because it looked like the kind of clue that mattered.")

    world.para()
    world.say(f"Then a tempest rolled over the roof and rattled the windows of {setting.place}.")
    world.say(f"{params.name} wanted to follow the trail at once, but the storm made the hall shine with rainwater and old shadows.")
    hero.memes["suspicion"] += 1
    world.say(f"Inside {params.name}'s head, a small voice said, 'If the clue gets wet, the whole case goes soft.'")

    if clue_at_risk(clue_cfg, setting):
        world.say(f"{params.name} glanced at the clue and frowned, because paper and tempest were bad neighbors.")

    protection = select_protection(clue_cfg, setting)
    if protection:
        world.say(f"{params.name}'s partner lifted {protection.phrase} from a shelf and said, 'Let's keep the evidence dry first.'")
        world.say(f"They chose to {protection.prep} before the search began.")
        hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
        clue.carried_by = None
        protected = world.add(Entity(
            id=protection.id,
            kind="thing",
            type="case",
            label=protection.label,
            phrase=protection.phrase,
            protective=True,
            plural=protection.plural,
            owner=hero.id,
        ))
        protected.carried_by = hero.id
        world.say(f"The clue went into {protection.label}, and the storm could huff all it wanted.")
    else:
        world.say(f"{params.name} had no proper case, so the detective had to trust quick hands and a quick mind.")

    propagate(world, narrate=True)

    world.para()
    world.say(f"{params.name} followed the clue from the desk drawer to the back hall, comparing every wet footprint with the memory in {params.name}'s head.")
    world.say(f"At last, the trail led to the window seat, where a frightened janitor had tucked the papered clue away so it would not blow into the rain.")

    world.say(f"Inside {params.name}'s head, the answer clicked: it was not theft at all, only rescue.")
    hero.memes["relief"] = 1.0
    world.say(f"{params.name} thanked the janitor, and the partner smiled because the case had a soft landing instead of a sharp one.")
    world.say(f"By the end, the papered clue was dry, the tempest still pounded the roof, and {params.name} walked home with a solved mystery and a bright, steady look.")

    world.facts.update(
        hero=hero,
        partner=partner,
        clue=clue,
        clue_cfg=clue_cfg,
        setting=setting,
        protection=protection,
        tempest=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short detective story for a child set in {f['setting'].place} during a tempest, with a papered clue and inner monologue.",
        f"Tell a mystery story where {f['hero'].id} worries that {f['clue_cfg'].label} might get ruined by rain, but the answer turns out gentle.",
        "Write a cozy detective tale that emphasizes careful thinking, a storm, and a clue that must stay dry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    clue = _safe_fact(world, f, "clue")
    setting = _safe_fact(world, f, "setting")
    hero_p = _hero_pronouns(hero.type)
    qa = [
        QAItem(
            question=f"Who is the detective in this story?",
            answer=f"The detective is {hero.id}, a {hero.memes.get('caution', 0.0) and 'careful' or 'sharp-eyed'} {hero.type} who keeps thinking about the case.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find?",
            answer=f"{hero.id} found {clue.phrase}, and it mattered because the clue was papered and had to stay dry.",
        ),
        QAItem(
            question=f"Why was the tempest a problem?",
            answer=f"The tempest was a problem because papered evidence can get wet and limp, which would make the clue harder to read and follow.",
        ),
    ]
    if f.get("protection"):
        prot = _safe_fact(world, f, "protection")
        qa.append(
            QAItem(
                question=f"How did {hero.id} protect the clue from the storm?",
                answer=f"{hero.id} and the partner used {prot.label} so the papered clue could stay dry while they searched.",
            )
        )
    qa.append(
        QAItem(
            question=f"What did {hero.id}'s inner monologue notice during the storm?",
            answer=f"Inside {hero.id}'s head, the detective noticed that if the clue got wet, the case would go soft, so staying dry had to come first.",
        )
    )
    qa.append(
        QAItem(
            question=f"What was the real answer at the end?",
            answer=f"The clue had not been stolen for selfish reasons; a frightened janitor had rescued it from the rain and tucked it away safely.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tempest?",
            answer="A tempest is a very strong storm with hard wind and heavy rain.",
        ),
        QAItem(
            question="Why do paper clues need care?",
            answer="Paper can get soft and wrinkled when it gets wet, so detectives try to keep paper clues dry.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and thinks hard to solve a mystery.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet thinking a character does in their own head.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is at risk when it is papered and the setting is not storm-safe.
at_risk(C,S) :- clue(C), papered(C), setting(S), not storm_safe(S).

% Protection is reasonable when it guards water/paper and can cover the clue.
fix(P,C,S) :- at_risk(C,S), protection(P), guards(P, water), guards(P, paper), covers(P, hands).

valid_story(S,C) :- at_risk(C,S), fix(P,C,S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.storm_safe:
            lines.append(asp.fact("storm_safe", sid))
        for act in sorted(s.affords):
            lines.append(asp.fact("affords", sid, act))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.papered:
            lines.append(asp.fact("papered", cid))
        if c.requires_dry:
            lines.append(asp.fact("requires_dry", cid))
    for p in PROTECTIONS:
        lines.append(asp.fact("protection", p.id))
        for g in sorted(p.guards):
            lines.append(asp.fact("guards", p.id, g))
        for c in sorted(p.covers):
            lines.append(asp.fact("covers", p.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(setting: Setting, clue: Clue) -> str:
    if not clue_at_risk(clue, setting):
        return "No story: that clue is already safe in that setting, so there is no storm problem to solve."
    return "No story: the requested combination has no honest protective fix."


def explain_gender(clue_id: str, gender: str) -> str:
    return f"(No story: {_safe_lookup(CLUES, clue_id).label} does not constrain gender here, but the requested mix was still unreasonable.)"


def valid_story_combos() -> list[tuple[str, str]]:
    out = []
    for s_id, s in SETTINGS.items():
        for c_id, c in CLUES.items():
            if clue_at_risk(c, s) and select_protection(c, s):
                out.append((s_id, c_id))
    return out


CURATED = [
    StoryParams(setting="dock", clue="map", name="Mina", gender="girl", trait="careful"),
    StoryParams(setting="dock", clue="note", name="Noah", gender="boy", trait="sharp-eyed"),
    StoryParams(setting="dock", clue="receipt", name="Iris", gender="girl", trait="patient"),
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


def build_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "clue", None):
        if not clue_at_risk(_safe_lookup(CLUES, getattr(args, "clue", None)), _safe_lookup(SETTINGS, getattr(args, "setting", None))):
            pass
    combos = [c for c in valid_story_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))]
    if not combos:
        pass
    setting, clue = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, name=name, gender=gender, trait=trait)


def build_parser_and_main() -> None:
    pass


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue) combos:")
        for s, c in combos:
            print(f"  {s:8} {c}")
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
                params = build_params_from_args(args, random.Random(seed))
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
