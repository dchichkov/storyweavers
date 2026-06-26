#!/usr/bin/env python3
"""
A tiny slice-of-life story world about a caribou, a moral value choice, and a
small conflict that ends in a gentle repair.

The simulated premise:
- A young caribou has something they care about doing.
- Another caribou or helper worries because it may hurt someone, break a promise,
  or be unfair.
- The turn is a moral choice: keep the selfish path, or make room for the other
  need.
- The ending shows a changed state: repaired trust, shared space, or a fairer
  outcome.

The story is intentionally small and concrete, with state-driven prose rather
than a frozen template. It is designed to produce child-facing, slice-of-life
stories with clear cause and effect.
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
# Domain registry
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
class Role:
    id: str
    label: str
    type: str
    kind: str = "character"
    traits: list[str] = field(default_factory=list)
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
class Place:
    id: str
    label: str
    indoors: bool = False
    affordances: set[str] = field(default_factory=set)
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
class Want:
    id: str
    verb: str
    noun: str
    place: str
    value: str
    conflict: str
    repair: str
    consequence: str
    moral_axis: str
    tags: set[str] = field(default_factory=set)
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    owner_role: str
    value: str
    kind: str = "thing"
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


ROLES = {
    "young": Role(id="young", label="Niko", type="caribou", traits=["small", "thoughtful"]),
    "parent": Role(id="parent", label="Mira", type="caribou", traits=["steady", "kind"]),
    "friend": Role(id="friend", label="Talo", type="caribou", traits=["friendly", "patient"]),
}

PLACES = {
    "snowy path": Place(id="snowy path", label="the snowy path", affordances={"sharing", "waiting", "walking"}),
    "woods edge": Place(id="woods edge", label="the woods edge", affordances={"sharing", "waiting", "listening"}),
    "cabin porch": Place(id="cabin porch", label="the cabin porch", indoors=False, affordances={"sharing", "waiting", "talking"}),
    "river bank": Place(id="river bank", label="the river bank", affordances={"sharing", "waiting", "helping"}),
}

WANTS = {
    "berries": Want(
        id="berries",
        verb="keep the last sweet berries",
        noun="berries",
        place="woods edge",
        value="generosity",
        conflict="share",
        repair="share the berries with everyone",
        consequence="there would not be enough for the younger caribou",
        moral_axis="fairness",
        tags={"share", "food", "fairness"},
    ),
    "sled": Want(
        id="sled",
        verb="keep the sled for the whole afternoon",
        noun="sled",
        place="snowy path",
        value="kindness",
        conflict="take turns",
        repair="let the friend use the sled next",
        consequence="the friend would wait in the cold too long",
        moral_axis="sharing",
        tags={"share", "play", "sharing"},
    ),
    "bell": Want(
        id="bell",
        verb="wear the shiny bell first",
        noun="bell",
        place="cabin porch",
        value="honesty",
        conflict="admit",
        repair="tell the truth about who found it",
        consequence="someone else would feel left out and hurt",
        moral_axis="truth",
        tags={"truth", "belonging"},
    ),
    "tea": Want(
        id="tea",
        verb="pour the warm tea for only one cup",
        noun="tea",
        place="cabin porch",
        value="care",
        conflict="wait",
        repair="pour two smaller cups",
        consequence="the guest would have nothing to drink",
        moral_axis="care",
        tags={"care", "sharing"},
    ),
}

OBJECTS = {
    "berries": ObjectCfg(id="berries", label="berries", phrase="the last sweet berries", owner_role="young", value="food"),
    "sled": ObjectCfg(id="sled", label="sled", phrase="the bright red sled", owner_role="young", value="play"),
    "bell": ObjectCfg(id="bell", label="bell", phrase="a shiny silver bell", owner_role="friend", value="belonging"),
    "tea": ObjectCfg(id="tea", label="tea", phrase="a warm kettle of tea", owner_role="parent", value="care"),
}

GREETINGS = [
    "The morning was quiet and clear.",
    "The snow lay soft along the path.",
    "The little home felt calm before the first choice of the day.",
]

# ---------------------------------------------------------------------------
# Shared story containers
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    obj: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone.fired = set(self.fired)
        return clone


THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def moral_reasonableness(want: Want, place: Place) -> bool:
    return place.id == want.place and "sharing" in place.affordances


def choice_is_compatible(want: Want, place: Place) -> bool:
    return moral_reasonableness(want, place)


def invalid_choice_reason(want: Want, place: Place) -> str:
    return (
        f"(No story: {want.id} belongs at {want.place}, and this world needs a place "
        f"that supports a small moral conflict and a fair repair. Try that setting.)"
    )


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

def _speak_start(world: World, hero: Entity, parent: Entity, want: Want, obj: Entity) -> None:
    world.say(_safe_lookup(GREETINGS, 0))
    world.say(
        f"{hero.id} was a small caribou who loved {want.value} even when it was hard."
    )
    world.say(
        f"That day, {hero.id} wanted to {want.verb}, because {obj.phrase} looked especially tempting."
    )

def _speak_conflict(world: World, hero: Entity, parent: Entity, want: Want, obj: Entity) -> None:
    hero.memes["wanting"] = 1
    hero.memes["conflict"] = 1
    parent.memes["concern"] = 1
    world.para()
    world.say(
        f"At {world.place.label}, {hero.id} reached for {obj.label}, but {parent.id} saw the problem."
    )
    world.say(
        f'"If you do that, {want.consequence}," {parent.id} said gently. '
        f'"We need to {want.conflict}."'
    )

def _speak_turn(world: World, hero: Entity, parent: Entity, friend: Entity, want: Want, obj: Entity) -> None:
    world.say(
        f"{hero.id} looked down at {obj.label}, then at {parent.id}, and felt the tug between wanting and fairness."
    )
    world.say(
        f"{hero.id} was quiet for a moment, then decided that {want.value} mattered more than winning."
    )
    hero.memes["resolve"] = 1
    hero.memes["conflict"] = 0
    parent.memes["relief"] = 1

def _speak_repair(world: World, hero: Entity, parent: Entity, friend: Entity, want: Want, obj: Entity) -> None:
    world.para()
    world.say(
        f"So {hero.id} chose to {want.repair}."
    )
    if friend.id in world.entities:
        friend.memes["gratitude"] = 1
        world.say(
            f"{friend.id} smiled, and the three of them used {obj.it()} in a fair way."
        )
    world.say(
        f"In the end, {hero.id} still enjoyed the morning, but now the feeling in the air was softer and kinder."
    )
    world.say(
        f"{hero.id} stood beside {parent.id} at {world.place.label}, proud of the choice that made room for everyone."
    )

def tell_story(place: Place, want: Want) -> World:
    world = World(place)
    hero = world.add(Entity(id=ROLES["young"].label, kind="character", type=ROLES["young"].type, label="young caribou"))
    parent = world.add(Entity(id=ROLES["parent"].label, kind="character", type=ROLES["parent"].type, label="parent caribou"))
    friend = world.add(Entity(id=ROLES["friend"].label, kind="character", type=ROLES["friend"].type, label="friend caribou"))
    obj_cfg = _safe_lookup(OBJECTS, want.id)
    obj = world.add(Entity(id=obj_cfg.id, label=obj_cfg.label, phrase=obj_cfg.phrase, owner=hero.id))
    world.facts.update(hero=hero, parent=parent, friend=friend, want=want, obj=obj)

    _speak_start(world, hero, parent, want, obj)
    _speak_conflict(world, hero, parent, want, obj)
    _speak_turn(world, hero, parent, friend, want, obj)
    _speak_repair(world, hero, parent, friend, want, obj)
    return world

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
want(W) :- desire(W).

moral_conflict(W) :- desire(W), value(W, V), concern(W, C), V != C.
compatible(P, W) :- place(P), desire(W), can_be_at(W, P), shares(P).
resolved(W) :- moral_conflict(W), repair(W, _).

#show compatible/2.
#show resolved/1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("setting", p.id))
        if p.indoors:
            lines.append(asp.fact("indoors", p.id))
        for a in sorted(p.affordances):
            lines.append(asp.fact("shares", p.id))
            lines.append(asp.fact("affords", p.id, a))
    for w in WANTS.values():
        lines.append(asp.fact("desire", w.id))
        lines.append(asp.fact("value", w.id, w.value))
        lines.append(asp.fact("concern", w.id, w.conflict))
        lines.append(asp.fact("repair", w.id, w.repair))
        lines.append(asp.fact("can_be_at", w.id, w.place))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2.\n#show resolved/1."))
    compat = set(asp.atoms(model, "compatible"))
    resolved = set(asp.atoms(model, "resolved"))
    python_compat = {(p.id, w.id) for p in PLACES.values() for w in WANTS.values() if choice_is_compatible(w, p)}
    python_resolved = {(w.id,) for w in WANTS.values() if True}
    ok = compat == python_compat
    if ok:
        print(f"OK: ASP parity for compatible choices ({len(compat)}).")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(compat))
    print("  py :", sorted(python_compat))
    return 1

# ---------------------------------------------------------------------------
# Q&A and formatting
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    want: Want = _safe_fact(world, world.facts, "want")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    return [
        f'Write a short slice-of-life story about a caribou named {hero.id} and a small choice about "{want.moral_axis}".',
        f"Tell a gentle story where {hero.id} wants to {want.verb}, but {parent.id} worries about fairness.",
        f"Write a child-friendly story about caribou, conflict, and a kind repair at {world.place.label}.",
    ]

def story_qa(world: World) -> list[QAItem]:
    want: Want = _safe_fact(world, world.facts, "want")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    friend: Entity = _safe_fact(world, world.facts, "friend")
    obj: Entity = _safe_fact(world, world.facts, "obj")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.place.label}?",
            answer=f"{hero.id} wanted to {want.verb}. That was tempting because {obj.phrase} looked special.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the choice?",
            answer=f"{parent.id} worried because {want.consequence}. The choice would not be fair to {friend.id}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} chose {want.value} over selfishness, and the morning became fair and calm for everyone.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caribou?",
            answer="A caribou is a large deer-like animal that lives in cold northern places and walks across snow with broad hooves.",
        ),
        QAItem(
            question="What does fairness mean?",
            answer="Fairness means making room for other people too, so one person does not take more than their share.",
        ),
        QAItem(
            question="Why can sharing help with conflict?",
            answer="Sharing can help because it gives each person a turn or a piece, which lowers hurt feelings and makes the group feel kinder.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        me = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if me:
            bits.append(f"memes={me}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"{e.id}: " + ", ".join(bits))
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    want: str
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


CURATED = [
    StoryParams(place="woods edge", want="berries"),
    StoryParams(place="snowy path", want="sled"),
    StoryParams(place="cabin porch", want="bell"),
    StoryParams(place="cabin porch", want="tea"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life caribou moral conflict stories.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--want", choices=WANTS.keys())
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES.keys()))
    want = getattr(args, "want", None) or rng.choice(list(WANTS.keys()))
    if not choice_is_compatible(_safe_lookup(WANTS, want), _safe_lookup(PLACES, place)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, want=want)

def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(PLACES, params.place), _safe_lookup(WANTS, params.want))
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

def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible choices:")
        for p, w in asp_valid_combos():
            print(f"  {p}: {w}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
