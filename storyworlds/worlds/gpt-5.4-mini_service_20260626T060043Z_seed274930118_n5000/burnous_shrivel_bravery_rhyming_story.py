#!/usr/bin/env python3
"""
A small storyworld about a brave child, a burnous, and a thing that shrivels.

The world is built for a tiny rhyming tale: a child loves their warm burnous,
the burnous is useful, but a bright heat or a careless wash can make it shrivel.
Bravery is the turn: the child faces the problem, asks for help, and finds a
gentle fix that keeps the ending bright.
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


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)


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

@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    burnous: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    name: str
    hot: bool = False
    windy: bool = False
    affords: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class ItemSpec:
    id: str
    label: str
    phrase: str
    kind: str
    region: str
    can_shrivel_from: set[str] = field(default_factory=set)
    can_hide_from: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
    name: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "courtyard": Place(name="the courtyard", hot=True, windy=False, affords={"rest", "walk"}),
    "dunes": Place(name="the dunes", hot=True, windy=True, affords={"rest", "walk"}),
    "tent": Place(name="the tent", hot=False, windy=False, affords={"rest", "sew"}),
}

ACTIONS = {
    "sun": {
        "verb": "sit in the hot sun",
        "gerund": "sitting in the hot sun",
        "risk": "shrivel",
        "cause": "the heat",
        "zone": {"torso"},
        "prompt": "sun",
        "tags": {"sun", "heat"},
    },
    "wash": {
        "verb": "wash the burnous",
        "gerund": "washing the burnous",
        "risk": "shrink",
        "cause": "the wash water",
        "zone": {"torso"},
        "prompt": "wash",
        "tags": {"wash", "water"},
    },
    "wind": {
        "verb": "hang it in the wind",
        "gerund": "hanging it in the wind",
        "risk": "flutter",
        "cause": "the gusts",
        "zone": {"torso"},
        "prompt": "wind",
        "tags": {"wind"},
    },
}

ITEMS = {
    "burnous": ItemSpec(
        id="burnous",
        label="burnous",
        phrase="a soft blue burnous",
        kind="burnous",
        region="torso",
        can_shrivel_from={"sun", "wash"},
        can_hide_from={"wind"},
    ),
}

GENTLE_FIXES = {
    ("sun", "burnous"): "shade",
    ("wash", "burnous"): "dry it flat",
    ("wind", "burnous"): "pin it down",
}

NAMES = ["Amina", "Samir", "Leila", "Yara", "Omar", "Mina"]
TRAITS = ["brave", "kind", "lively", "gentle", "steady"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The burnous is at risk when the chosen action can harm it.
at_risk(A, I) :- action(A), item(I), action_harms(A, I).

% A fix is sensible only when it matches the specific danger.
has_fix(A, I) :- action(A), item(I), action_fix(A, I).

valid_story(P, A, I) :- place(P), action(A), item(I), can_story(P, A, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.hot:
            lines.append(asp.fact("hot", pid))
        if p.windy:
            lines.append(asp.fact("windy", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("region", iid, it.region))
        for a in sorted(it.can_shrivel_from):
            lines.append(asp.fact("action_harms", a, iid))
            lines.append(asp.fact("action_fix", a, iid, _safe_lookup(GENTLE_FIXES, (a, iid))))
    for (a, i), fix in GENTLE_FIXES.items():
        lines.append(asp.fact("action_fix", a, i, fix))
    for p in PLACES:
        for a in ACTIONS:
            for i in ITEMS:
                lines.append(asp.fact("can_story", p, a, i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo = set(asp.atoms(model, "valid_story"))
    if py == clingo:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - clingo))
    print("asp-only:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for a in ACTIONS:
            for i in ITEMS:
                if reasonableness_gate(p, a, i):
                    combos.append((p, a, i))
    return combos


def reasonableness_gate(place_id: str, action_id: str, item_id: str) -> bool:
    place = _safe_lookup(PLACES, place_id)
    action = _safe_lookup(ACTIONS, action_id)
    item = _safe_lookup(ITEMS, item_id)
    return action_id in place.affords and item_id == "burnous" and (
        action_id in item.can_shrivel_from or action_id in item.can_hide_from
    )


def choose_fix(action_id: str, item_id: str) -> Optional[str]:
    return GENTLE_FIXES.get((action_id, item_id))


def tell(place: Place, action_id: str, item_spec: ItemSpec, name: str) -> World:
    w = World(place)
    hero = w.add(Entity(id=name, kind="character", label=name))
    burnous = w.add(Entity(
        id=item_spec.id,
        label=item_spec.label,
        phrase=item_spec.phrase,
        owner=hero.id,
        worn_by=hero.id,
        protective=True,
    ))

    hero.memes["bravery"] = 1.0
    w.say(f"{hero.id} wore {burnous.phrase} and stepped out with a bright little grin.")
    w.say(f"The day was about {action_id}, and the breeze around {place.name} could turn tricky.")

    if action_id == "sun":
        w.say(f"{hero.id} wanted to sit in the hot sun and listen to the sand go hush-hush.")
    elif action_id == "wash":
        w.say(f"{hero.id} wanted to wash the burnous so it would look neat and neat again.")
    else:
        w.say(f"{hero.id} wanted to hang it in the wind and watch it dance like a kite.")

    if action_id in item_spec.can_shrivel_from:
        if action_id == "sun":
            burnous.meters["shrivel"] = 1.0
            w.say(f"But the heat was a bully to cloth, and the burnous began to shrivel.")
        elif action_id == "wash":
            burnous.meters["shrivel"] = 1.0
            w.say(f"But the wash water was too keen, and the burnous came out shrunk and small.")
        else:
            burnous.meters["shrivel"] = 1.0
            w.say(f"The gusts worried the cloth, and the burnous fluttered into a wrinkled twist.")
    else:
        w.say(f"The burnous stayed steady, safe, and smooth.")

    fix = choose_fix(action_id, item_spec.id)
    if burnous.meters.get("shrivel", 0) >= 1.0 and fix:
        hero.memes["bravery"] += 1.0
        w.say(f"{hero.id} took a brave breath and chose a kinder way: {fix}.")
        if action_id == "sun":
            w.say(f"Under a cool shade, the burnous rested, and its edges stopped their shrinky race.")
        elif action_id == "wash":
            w.say(f"{hero.id} laid it flat to dry, and the burnous uncurled with a patient sigh.")
        else:
            w.say(f"{hero.id} pinned it down, and the stubborn wind lost its game at last.")
        burnous.meters["shrivel"] = 0.0
        hero.memes["joy"] = 1.0
        w.say(f"Now {hero.id} could smile again, and the burnous looked long and lovely.")
    elif burnous.meters.get("shrivel", 0) >= 1.0:
        w.say(f"{hero.id} frowned, but then asked for help, because brave hearts do not hide.")
        burnous.meters["shrivel"] = 0.5

    w.facts = {
        "hero": hero,
        "item": burnous,
        "action_id": action_id,
        "place": place,
        "fix": fix,
    }
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    return [
        f'Write a short rhyming story for a young child that includes "{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item").label}" and "bravery".',
        f"Tell a gentle tale about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} and a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item").label} that starts to shrivel.",
        f"Write a cozy story where a child faces {_safe_lookup(ACTIONS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action_id"))['cause']} with bravery and a burnous.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    item: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    action_id: str = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action_id")
    fix = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fix")
    action = _safe_lookup(ACTIONS, action_id)
    qa = [
        QAItem(
            question=f"What did {hero.id} wear in the story?",
            answer=f"{hero.id} wore {item.phrase}, a burnous that mattered to the story from the very start.",
        ),
        QAItem(
            question=f"What problem did the burnous have during the {action['prompt']} part?",
            answer=f"The burnous began to {action['risk']} because of {action['cause']}.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} stayed calm, asked for a kinder fix, and chose {fix} instead of giving up.",
        ),
    ]
    if item.meters.get("shrivel", 0) == 0.0:
        qa.append(QAItem(
            question=f"What did the burnous look like at the end?",
            answer="It looked smooth and safe again, so the ending image proved the problem had been solved.",
        ))
    return qa


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a burnous?",
            answer="A burnous is a loose outer cloak or robe that can keep a person warm and covered.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means facing a hard moment with a steady heart instead of running away.",
        ),
        QAItem(
            question="What does shrivel mean?",
            answer="To shrivel is to get smaller, wrinkled, or folded up, often because of heat or drying out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(w: World) -> str:
    lines = ["--- trace ---"]
    for e in w.entities.values():
        lines.append(f"{e.id}: kind={e.kind} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def rhyme_story(w: World) -> str:
    return w.render()


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about burnous and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name", choices=NAMES)
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "action", None) and getattr(args, "item", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "action", None), getattr(args, "item", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    valid = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
        and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
    ]
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, item = rng.choice(valid)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, action=action, item=item, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), params.action, _safe_lookup(ITEMS, params.item), params.name)
    story = rhyme_story(world)
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(place="courtyard", action="sun", item="burnous", name="Amina"),
    StoryParams(place="tent", action="wash", item="burnous", name="Leila"),
    StoryParams(place="dunes", action="wind", item="burnous", name="Omar"),
]


def asp_verify_gate() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo = set(asp.atoms(model, "valid_story"))
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python-only:", sorted(py - clingo))
    print("clingo-only:", sorted(clingo - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_gate())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for s in stories:
            print(s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.action} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
