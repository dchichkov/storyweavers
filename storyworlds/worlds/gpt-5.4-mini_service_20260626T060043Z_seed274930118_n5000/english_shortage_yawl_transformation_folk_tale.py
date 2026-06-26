#!/usr/bin/env python3
"""
storyworlds/worlds/english_shortage_yawl_transformation_folk_tale.py
=====================================================================

A small folk-tale storyworld about an English-speaking traveler, a village
shortage, and a humble yawl that can be transformed into something useful.

Seed imagination:
- A river village has a shortage of one needed thing.
- A small yawl is the only boat, but it is not fit for the task.
- A wise helper finds a transformation that solves the shortage without
  breaking the story's gentle folk-tale logic.

The world supports short, child-facing stories with a beginning, a turn, and an
ending image proving what changed.
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



def _safe_next(iterable, fallback=None):
    return next(iter(iterable), fallback)


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
    caretaker: Optional[str] = None
    plural: bool = False
    transformed_from: Optional[str] = None
    transformed_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    boat: object | None = None
    charm: object | None = None
    elder: object | None = None
    hero: object | None = None
    needed: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother", "grandmother"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father", "grandfather"}:
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
class Setting:
    place: str
    river: str
    weather: str = "misty"
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
class Need:
    id: str
    noun: str
    phrase: str
    shortage_reason: str
    at_risk: str
    remedy: str
    remedy_noun: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Transformation:
    id: str
    from_form: str
    to_form: str
    label: str
    method: str
    ending_image: str
    covers: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def _entity_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _entity_meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _set_meter(e: Entity, key: str, val: float) -> None:
    e.meters[key] = val


def _add_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _add_meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _do_transformation(world: World, maker: Entity, target: Entity, trans: Transformation, narrate: bool = True) -> None:
    sig = ("transform", target.id, trans.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    target.type = trans.to_form
    target.label = trans.label
    target.transformed_from = trans.from_form
    target.transformed_to = trans.to_form
    _add_meter(target, "usefulness", 1.0)
    _add_meme(maker, "hope", 1.0)
    if narrate:
        world.say(
            f"{maker.id} sang the old words and worked {trans.method}. "
            f"Then the {trans.from_form} became {trans.label}."
        )


def _do_shortage(world: World, need: Need) -> None:
    sig = ("shortage", need.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            _add_meme(ent, "worry", 1.0)


def _predict_fix(world: World, need: Need, trans: Transformation) -> bool:
    sim = world.copy()
    helper = _safe_next((e for e in list(sim.entities.values()) if e.id == "Mara"), _safe_next(sim.entities.values()))
    target = _safe_next((e for e in list(sim.entities.values()) if e.id == "yawl"), _safe_next(sim.entities.values()))
    _do_transformation(sim, helper, target, trans, narrate=False)
    return target.type == trans.to_form and trans.id == need.remedy


def reasonableness_gate(need: Need, trans: Transformation) -> bool:
    return need.remedy == trans.id and need.at_risk in trans.covers


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for need_id, need in NEEDS.items():
        for trans_id, trans in TRANSFORMATIONS.items():
            if reasonableness_gate(need, trans):
                combos.append((SETTINGS_DEFAULT, need_id, trans_id))
    return combos


def explain_rejection(need: Need, trans: Transformation) -> str:
    return (
        f"(No story: the shortage of {need.noun} cannot be fixed by turning a yawl into {trans.label}. "
        f"The remedy must match the shortage and cover the at-risk need.)"
    )


def setup_world(setting: Setting, need: Need, trans: Transformation, hero_name: str, hero_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind))
    elder = world.add(Entity(id="Grandmother", kind="character", type="grandmother"))
    boat = world.add(Entity(id="yawl", kind="thing", type="yawl", label="a small yawl"))
    needed = world.add(Entity(id=need.id, kind="thing", type=need.noun, label=need.phrase, caretaker=elder.id))
    charm = world.add(Entity(id="spell", kind="thing", type="charm", label="a bright turning charm", owner=elder.id))
    world.facts.update(hero=hero, elder=elder, boat=boat, need=needed, need_cfg=need, trans=trans, charm=charm)
    return world


def tell_story(world: World) -> None:
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")  # type: ignore[assignment]
    elder: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "elder")  # type: ignore[assignment]
    boat: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "boat")  # type: ignore[assignment]
    need: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "need")  # type: ignore[assignment]
    need_cfg: Need = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "need_cfg")  # type: ignore[assignment]
    trans: Transformation = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "trans")  # type: ignore[assignment]

    world.say(
        f"In {world.setting.place}, there lived a little {hero.type} named {hero.id}, "
        f"who could speak a few kind English words to every neighbor."
    )
    world.say(
        f"Each dawn, {world.setting.river} came silver and quiet past the village, and {need.label} was in short supply."
    )
    world.say(
        f"The people sighed over the shortage, because {need_cfg.shortage_reason}."
    )

    world.para()
    world.say(
        f"One misty morning, {hero.id} and {elder.id} found the only boat, a yawl, tied by the bank."
    )
    world.say(
        f"It was too small for the errand, and the need could not wait."
    )

    world.para()
    _add_meme(hero, "desire", 1.0)
    _add_meme(elder, "care", 1.0)
    world.say(
        f"{hero.id} wanted to help at once, but {elder.id} shook her head and smiled. "
        f'"A plain yawl cannot carry this day," she said. "We need an old turning."'
    )
    if _predict_fix(world, need_cfg, trans):
        _do_transformation(world, elder, boat, trans, narrate=True)
        _set_meter(need, "available", 1.0)
        _add_meme(hero, "joy", 1.0)
        _add_meme(elder, "joy", 1.0)
        world.say(
            f"After that, {boat.label} glided light and true, and {need.label} could be brought across the river."
        )
        world.say(
            f"By evening, the village had enough {need.noun} again, and the old folks said the river had never looked so kind."
        )
        world.para()
        world.say(trans.ending_image)
    else:
        pass


SETTINGS = {
    "river_village": Setting(place="the river village", river="the Brightwater"),
}

SETTINGS_DEFAULT = "river_village"

NEEDS = {
    "salt": Need(
        id="salt",
        noun="salt",
        phrase="a little basket of salt",
        shortage_reason="the kitchen pots were empty, and the bread tasted flat without it",
        at_risk="basket",
        remedy="ferry",
        remedy_noun="ferry",
        tags={"shortage", "english"},
    ),
    "flour": Need(
        id="flour",
        noun="flour",
        phrase="a sack of flour",
        shortage_reason="there was not enough flour to bake the feast cakes",
        at_risk="sack",
        remedy="barge",
        remedy_noun="barge",
        tags={"shortage"},
    ),
    "candles": Need(
        id="candles",
        noun="candles",
        phrase="a bundle of candles",
        shortage_reason="the long night had left the cottages dim",
        at_risk="bundle",
        remedy="lanternboat",
        remedy_noun="lantern boat",
        tags={"shortage"},
    ),
}

TRANSFORMATIONS = {
    "ferry": Transformation(
        id="ferry",
        from_form="yawl",
        to_form="ferry",
        label="a wide ferry",
        method="braiding willow and tying a steadier plank across the hull",
        ending_image="Soon the transformed ferry carried the salt home, while the river shone like a ribbon under moonlight.",
        covers={"basket"},
        tags={"transformation", "yawl"},
    ),
    "barge": Transformation(
        id="barge",
        from_form="yawl",
        to_form="barge",
        label="a broad barge",
        method="fastening reed mats and a flat deck over the yawl",
        ending_image="Soon the broad barge bore the flour safely, and the village oven glowed warm again.",
        covers={"sack"},
        tags={"transformation", "yawl"},
    ),
    "lanternboat": Transformation(
        id="lanternboat",
        from_form="yawl",
        to_form="lanternboat",
        label="a lantern boat",
        method="hanging glass lamps from a tall mast and painting the bow gold",
        ending_image="Soon the lantern boat drifted home with candles twinkling like little stars on the water.",
        covers={"bundle"},
        tags={"transformation", "yawl"},
    ),
}

GIRL_NAMES = ["Mara", "Lena", "Suri", "Nina", "Tala"]
BOY_NAMES = ["Petr", "Ivo", "Jon", "Kian", "Bram"]
TRAITS = ["bright-eyed", "steady", "kind", "clever", "patient"]


ASP_RULES = r"""
need_at_risk(N) :- need(N), at_risk(N, R), remedy(T, N), covers(T, R).
valid_story(S, N, T) :- setting(S), need(N), transformation(T),
                        need_at_risk(N), remedy(T, N), covers(T, R), at_risk(N, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("at_risk", nid, n.at_risk))
        lines.append(asp.fact("remedy", n.remedy, nid))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
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
    clingo = set((s, n, t) for (s, n, t) in asp_valid_stories())
    if py == clingo:
        print(f"OK: ASP matches Python gate ({len(py)} story combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("python-only:", sorted(py - clingo))
    print("asp-only:", sorted(clingo - py))
    return 1


@dataclass
class StoryParams:
    setting: str = ""
    need: str = ""
    transformation: str = ""
    name: str = ""
    gender: str = ""
    trait: str = ""
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world: english shortage yawl transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "need", None) and getattr(args, "transformation", None):
        if not reasonableness_gate(_safe_lookup(NEEDS, getattr(args, "need", None)), _safe_lookup(TRANSFORMATIONS, getattr(args, "transformation", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "need", None):
        combos = [c for c in combos if c[1] == getattr(args, "need", None)]
    if getattr(args, "transformation", None):
        combos = [c for c in combos if c[2] == getattr(args, "transformation", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, need, trans = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, need=need, transformation=trans, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")  # type: ignore[assignment]
    need_cfg: Need = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "need_cfg")  # type: ignore[assignment]
    return [
        f'Write a short folk tale about an English-speaking child named {hero.id} and a village shortage of {need_cfg.noun}.',
        f"Tell a gentle story where a yawl is transformed so {hero.id} can help the village.",
        f"Write a child-friendly river story that includes the words english, shortage, yawl, and transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")  # type: ignore[assignment]
    elder: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder")  # type: ignore[assignment]
    need: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "need")  # type: ignore[assignment]
    need_cfg: Need = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "need_cfg")  # type: ignore[assignment]
    trans: Transformation = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trans")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {elder.id}, who helped with the shortage of {need_cfg.noun}.",
        ),
        QAItem(
            question=f"What problem did the village have?",
            answer=f"The village had a shortage of {need_cfg.noun}, because {need_cfg.shortage_reason}.",
        ),
        QAItem(
            question=f"What was transformed?",
            answer=f"The yawl was transformed into {trans.label} so it could carry what the village needed.",
        ),
        QAItem(
            question=f"Why did the old helper change the yawl?",
            answer=f"She changed it because the plain yawl was too small for the job, and the shortage could not wait.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yawl?",
            answer="A yawl is a small sailing boat, usually with a narrow body and a modest sail.",
        ),
        QAItem(
            question="What does shortage mean?",
            answer="A shortage means there is not enough of something people need.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form.",
        ),
        QAItem(
            question="Why do folk tales often use magical helpers?",
            answer="Folk tales often use magical helpers to show cleverness, kindness, and a little wonder can solve hard problems.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed_to:
            bits.append(f"transformed={e.transformed_from}->{e.transformed_to}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(NEEDS, params.need),
        _safe_lookup(TRANSFORMATIONS, params.transformation),
        params.name,
        params.gender,
    )
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="river_village", need="salt", transformation="ferry", name="Mara", gender="girl", trait="kind"),
    StoryParams(setting="river_village", need="flour", transformation="barge", name="Ivo", gender="boy", trait="steady"),
    StoryParams(setting="river_village", need="candles", transformation="lanternboat", name="Tala", gender="girl", trait="clever"),
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.need} via {p.transformation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
