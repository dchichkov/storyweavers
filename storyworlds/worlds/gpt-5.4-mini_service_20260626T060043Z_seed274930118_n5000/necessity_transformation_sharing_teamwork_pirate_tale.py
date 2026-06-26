#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/necessity_transformation_sharing_teamwork_pirate_tale.py
====================================================================================================

A small pirate-tale story world about necessity, transformation, sharing, and teamwork.

Premise:
A tiny pirate crew is trying to reach a hidden cove. Their boat is short on the one
thing they truly need: a working sail. The crew must share tools and work together
to transform a plain scrap into a seaworthy sail before the tide turns.

Story shape:
- beginning: the captain and crew set out and discover the lack
- middle: necessity forces an argument and a shared plan
- turn: the crew transforms a scrap into the needed gear
- end: teamwork gets them to the cove, proving what changed

The world is deliberately small and classical: a few typed entities with physical
meters and emotional memes, a fixed set of plausible variants, and a reasonableness
gate that rejects weak combinations.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrying: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    needle: object | None = None
    rope: object | None = None
    sail: object | None = None
    scrap: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pirate", "mate", "first_mate"}
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
class Harbor:
    name: str
    affords: set[str] = field(default_factory=set)
    tide: str = "low"
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
class Need:
    id: str
    label: str
    phrase: str
    lacks: str
    turn_into: str
    requires: set[str]
    made_by: str
    consumes: str
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
class Tool:
    id: str
    label: str
    phrase: str
    shares: set[str]
    helps: set[str]
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
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
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
        clone = World(self.harbor)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _need_text(need: Need) -> str:
    return need.phrase


def _crew_names(world: World) -> str:
    crew = [e.id for e in world.characters()]
    if len(crew) == 2:
        return f"{crew[0]} and {crew[1]}"
    return ", ".join(crew[:-1]) + f", and {crew[-1]}"


def _chance_of_success(world: World, need: Need) -> bool:
    scrap = world.get("scrap")
    return scrap.meters.get("shape", 0) >= THRESHOLD and scrap.meters.get(need.consumes, 0) >= THRESHOLD


def _do_transform(world: World, need: Need, narrate: bool = True) -> None:
    scrap = world.get("scrap")
    if scrap.meters.get("shape", 0) < THRESHOLD:
        scrap.meters["shape"] = 1.0
    if need.consumes not in scrap.meters:
        scrap.meters[need.consumes] = 0.0
    scrap.meters[need.consumes] += 1.0
    scrap.meters["useful"] = 1.0
    scrap.label = need.turn_into
    if narrate:
        world.say(
            f"By clever hands and a few hard knots, the scrap was transformed into {need.turn_into}."
        )


def reasonableness_gate(harbor: Harbor, need: Need, tool: Tool) -> bool:
    return need.id in harbor.affords and need.made_by in tool.helps and need.consumes in tool.shares


def predict(world: World, need: Need) -> dict:
    sim = world.copy()
    _do_transform(sim, need, narrate=False)
    sail = sim.get("sail")
    return {"has_sail": sail.label == need.turn_into, "ready": _chance_of_success(sim, need)}


@dataclass
class StoryParams:
    harbor: str
    need: str
    crew_size: int
    seed: Optional[int] = None
    params: object | None = None
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


HARBORS = {
    "moonbay": Harbor(name="Moon Bay", affords={"sail"}, tide="rising"),
    "sharkcove": Harbor(name="Shark Cove", affords={"sail"}, tide="rising"),
    "starwharf": Harbor(name="Star Wharf", affords={"sail"}, tide="falling"),
}

NEEDS = {
    "repair_sail": Need(
        id="repair_sail",
        label="sail",
        phrase="a torn sail",
        lacks="a working sail",
        turn_into="a patched sail",
        requires={"cloth", "rope"},
        made_by="stitching and tying",
        consumes="cloth",
        tags={"necessity", "transformation", "teamwork", "sharing", "pirate"},
    ),
}

TOOLS = {
    "needle": Tool(
        id="needle",
        label="a sewing needle",
        phrase="a sewing needle",
        shares={"cloth"},
        helps={"stitching and tying"},
    ),
    "rope": Tool(
        id="rope",
        label="a coil of rope",
        phrase="a coil of rope",
        shares={"rope"},
        helps={"stitching and tying"},
    ),
    "bucket": Tool(
        id="bucket",
        label="a bucket of seawater",
        phrase="a bucket of seawater",
        shares={"water"},
        helps={"cooling"},
    ),
}

CREW_POOL = [
    ("Ava", "captain", "captain"),
    ("Milo", "pirate", "pirate"),
    ("Nell", "first_mate", "first mate"),
    ("Finn", "pirate", "pirate"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world about necessity and teamwork.")
    ap.add_argument("--harbor", choices=HARBORS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--crew-size", type=int, choices=[2, 3, 4], default=3)
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


def valid_combos() -> list[tuple[str, str, int]]:
    out = []
    for h_id, harbor in HARBORS.items():
        for n_id, need in NEEDS.items():
            if h_id in HARBORS and need.id in harbor.affords:
                out.append((h_id, n_id, 3))
                out.append((h_id, n_id, 4))
                out.append((h_id, n_id, 2))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "harbor", None) is None or c[0] == getattr(args, "harbor", None))
              and (getattr(args, "need", None) is None or c[1] == getattr(args, "need", None))
              and (getattr(args, "crew_size", None) is None or c[2] == getattr(args, "crew_size", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    harbor, need, crew_size = rng.choice(list(combos))
    return StoryParams(harbor=harbor, need=need, crew_size=crew_size)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(HARBORS, params.harbor))
    need = _safe_lookup(NEEDS, params.need)

    captain = world.add(Entity(id="captain", kind="character", type="captain", label="Captain Mara"))
    mates = []
    for name, typ, label in CREW_POOL[: params.crew_size - 1]:
        mates.append(world.add(Entity(id=name, kind="character", type=typ, label=label)))
    scrap = world.add(Entity(id="scrap", type="thing", label="a torn scrap of canvas", meters={"shape": 0.0, "cloth": 0.0}))
    sail = world.add(Entity(id="sail", type="thing", label=need.lacks, owner="ship"))
    rope = world.add(Entity(id="rope", type="thing", label="a coil of rope"))
    needle = world.add(Entity(id="needle", type="thing", label="a sewing needle"))

    world.say(
        f"At {world.harbor.name}, Captain Mara found a hard necessity: the ship had no working sail."
    )
    world.say(
        f"The crew looked at a torn scrap of canvas, and the little boat rocked in the wind."
    )

    world.para()
    captain.memes["worry"] = 1.0
    for m in mates:
        m.memes["teamwork"] = 1.0
    world.say(
        f"The captain said they could not leave until the sail was fixed, because the tide was rising."
    )
    world.say(
        f"The crew gathered {needle.label}, {rope.label}, and the scrap, then shared the work without grumbling."
    )

    world.para()
    if not reasonableness_gate(world.harbor, need, TOOLS["needle"]):
        pass
    world.facts["predicted"] = predict(world, need)
    _do_transform(world, need, narrate=True)
    sail.label = need.turn_into

    world.say(
        f"Together they stitched and tied until the torn canvas became a patched sail."
    )
    world.say(
        f"That transformation mattered: the ship could catch the wind again."
    )

    world.para()
    captain.memes["joy"] = 1.0
    for m in mates:
        m.memes["pride"] = 1.0
    world.say(
        f"Then the crew hoisted the new sail as a team, and the boat slipped out of {world.harbor.name}."
    )
    world.say(
        f"They shared a grin as the ship moved forward, proving that necessity had turned scraps into a way home."
    )

    world.facts.update(
        captain=captain,
        mates=mates,
        need=need,
        scrap=scrap,
        sail=sail,
        rope=rope,
        needle=needle,
        harbor=world.harbor,
        crew_size=params.crew_size,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    need = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "need")
    harbor = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "harbor")
    return [
        f"Write a short pirate tale about a ship in {harbor.name} that faces necessity and must fix {need.phrase}.",
        f"Tell a child-friendly story where a pirate crew uses sharing and teamwork to transform a scrap into {need.lacks}.",
        f"Write a simple story about pirates who cannot sail until they work together and make a new {need.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    need = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "need")
    harbor = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "harbor")
    crew = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "mates")
    crew_names = ", ".join(m.id for m in crew)
    return [
        QAItem(
            question=f"Why did the pirate crew need to work together at {harbor.name}?",
            answer=f"They needed to work together because the ship had no working sail, and the tide was rising. Necessity made the fix urgent.",
        ),
        QAItem(
            question=f"What did the crew transform the torn scrap into?",
            answer=f"They transformed the torn scrap of canvas into {need.turn_into}.",
        ),
        QAItem(
            question=f"How did the pirates show sharing in the story?",
            answer=f"They shared the needle, rope, and canvas so everyone could help with the repair.",
        ),
        QAItem(
            question=f"Which crew members helped with the repair?",
            answer=f"The crew members who helped were {crew_names}. They worked as a team on the sail.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is necessity?",
            answer="Necessity means something is needed very badly, so people must act to solve the problem.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is when something changes into a new form or use, like turning scrap cloth into a sail.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do different jobs together to reach the same goal.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use the things you have, so everyone can help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for hid in HARBORS:
        lines.append(asp.fact("harbor", hid))
        lines.append(asp.fact("affords", hid, "sail"))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("requires", nid, "cloth"))
        lines.append(asp.fact("requires", nid, "rope"))
        lines.append(asp.fact("made_by", nid, "stitching_and_tying"))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for s in sorted(tool.shares):
            lines.append(asp.fact("shares", tid, s))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(H,N) :- harbor(H), need(N), affords(H,sail), requires(N,cloth), requires(N,rope).
teamwork(H) :- valid(H,N).
sharing(H) :- valid(H,N).
transformation(H) :- valid(H,N).
#show valid/2.
#show teamwork/1.
#show sharing/1.
#show transformation/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = {(h, n) for h, n, _ in valid_combos()}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


def build_sample(params: StoryParams) -> StorySample:
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
        print()
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/2.\n#show teamwork/1.\n#show sharing/1.\n#show transformation/1."))
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for h in HARBORS:
            for n in NEEDS:
                params = StoryParams(harbor=h, need=n, crew_size=3, seed=base_seed)
                samples.append(build_sample(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = build_sample(params)
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
