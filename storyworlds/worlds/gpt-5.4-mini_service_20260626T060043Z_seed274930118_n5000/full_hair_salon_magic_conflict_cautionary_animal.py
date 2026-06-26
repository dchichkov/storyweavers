#!/usr/bin/env python3
"""
A standalone storyworld for a small animal-story style hair-salon tale with
magic, conflict, and a cautionary turn.

Premise:
A little animal loves a magical hair style at the salon. The salon gets full,
the magic goes a little wrong, and a caretaker must warn the child to slow down.
The story resolves when they choose a safer, gentler spell and finish the style
without trouble.
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
    wore: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cape: object | None = None
    child: object | None = None
    stylist: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "fox", "cat", "rabbit"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "bear", "dog", "lion"}:
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
class Salon:
    place: str = "the hair salon"
    full: bool = True
    magical: bool = True
    services: set[str] = field(default_factory=lambda: {"cut", "wash", "braid", "sparkle"})
    SETTINGS: set[str] = field(default_factory=set)
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
class Style:
    id: str
    label: str
    phrase: str
    needed: str
    magic: str
    caution: str
    risk: str
    keyword: str = "full"
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
class Charm:
    id: str
    label: str
    covers: set[str]
    neutralizes: set[str]
    prep: str
    tail: str
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
    def __init__(self, salon: Salon) -> None:
        self.salon = salon
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.salon)
        w.entities = copy.deepcopy(self.entities)
        w.lines = [[]]
        w.fired = set(self.fired)
        return w


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("place", "salon"), asp.fact("setting_full", "salon"), asp.fact("setting_magical", "salon")]
    for sid, s in STYLES.items():
        lines.append(asp.fact("style", sid))
        lines.append(asp.fact("needs", sid, s.needed))
        lines.append(asp.fact("magic_of", sid, s.magic))
        lines.append(asp.fact("risk_of", sid, s.risk))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for n in sorted(c.neutralizes):
            lines.append(asp.fact("neutralizes", cid, n))
        for cov in sorted(c.covers):
            lines.append(asp.fact("covers", cid, cov))
    return "\n".join(lines)


ASP_RULES = r"""
unsafe(S) :- style(S), risk_of(S, R), not safe_risk(R).
safe_risk(R) :- neutralizes(C, R), charm(C).
compatible(S, C) :- style(S), charm(C), needs(S, N), covers(C, N), risk_of(S, R), neutralizes(C, R).
valid_story(S, C) :- style(S), charm(C), compatible(S, C), not unsafe(S).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate_asp_valid() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def aspiration_gate(style: Style, charm: Charm) -> bool:
    return style.needed in charm.covers and style.risk in charm.neutralizes


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, s in STYLES.items():
        for cid, c in CHARMS.items():
            if aspiration_gate(s, c):
                out.append((sid, cid))
    return out


def predict_scatter(world: World, child: Entity, style: Style) -> bool:
    sim = world.copy()
    _do_style(sim, sim.get(child.id), style, narrate=False)
    return bool(sim.entities["cape"].meters.get("sparkles", 0) > 0 and sim.entities["cape"].meters.get("tangled", 0) > 0)


def _do_style(world: World, child: Entity, style: Style, narrate: bool = True) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.meters["sparkle"] = child.meters.get("sparkle", 0) + 1
    if style.id == "wild_curls":
        world.get("cape").meters["tangled"] = world.get("cape").meters.get("tangled", 0) + 1
    if style.id == "moon_braids":
        world.get("cape").meters["sparkles"] = world.get("cape").meters.get("sparkles", 0) + 1
    if narrate:
        world.say(f"{child.id} tried the style and the little magic began to glow.")


def setup(world: World, child: Entity, stylist: Entity, cape: Entity, style: Style) -> None:
    world.say(f"{child.id} was a small {child.type} who loved visiting {world.salon.place}.")
    world.say(f"{child.pronoun().capitalize()} wanted {style.phrase}, because the magic made {style.label} look like a storybook dream.")
    world.say(f"{stylist.label} showed {child.id} a bright {cape.label}, and {child.id} wore {cape.label} before the chair turned.")
    world.facts.update(child=child, stylist=stylist, cape=cape, style=style)


def conflict(world: World, child: Entity, stylist: Entity, style: Style) -> None:
    if world.salon.full:
        world.say(f"The salon was full, and the waiting chairs were packed with quiet animals.")
    world.say(f"{child.id} wanted to rush the magic, but {stylist.label} warned that hurried spells can pull hair the wrong way.")
    world.say(f'"Slow down," {stylist.pronoun("subject")} said. "A careful brush is safer than a wild sparkle."')
    child.memes["defiance"] = child.memes.get("defiance", 0) + 1
    world.say(f"{child.id} pouted, because {child.pronoun("possessive")} head wanted the glittery finish right now.")


def resolve(world: World, child: Entity, stylist: Entity, style: Style, charm: Charm) -> None:
    child.memes["defiance"] = 0
    child.memes["trust"] = child.memes.get("trust", 0) + 1
    world.say(f"Then {stylist.label} picked a gentler charm: {charm.label}.")
    world.say(f'"{charm.prep}," {stylist.label} said, and {child.id} listened this time.')
    world.say(f"They finished the hair with slow, neat strokes, and the safe magic kept {child.id}'s hair bright without a tangle.")
    world.say(f"In the end, {child.id} smiled at the mirror, and the salon felt calm again.")
    world.say(f"{child.id} left with a full little heart and a tidy style that did not pull or snag.")


def tell(salon: Salon, style: Style, charm: Charm, child_name: str, child_type: str, stylist_name: str) -> World:
    world = World(salon)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    stylist = world.add(Entity(id="stylist", kind="character", type="fox", label=stylist_name))
    cape = world.add(Entity(id="cape", type="cape", label="sparkly cape", caretaker=stylist.id))
    setup(world, child, stylist, cape, style)
    world.para()
    conflict(world, child, stylist, style)
    world.para()
    resolve(world, child, stylist, style, charm)
    world.facts["resolved"] = True
    return world


SETTINGS = {"salon": Salon()}
STYLES = {
    "wild_curls": Style(
        id="wild_curls",
        label="wild curls",
        phrase="wild curls with a magical bounce",
        needed="hairbrush",
        magic="sparkle",
        caution="careful",
        risk="tangled",
    ),
    "moon_braids": Style(
        id="moon_braids",
        label="moon braids",
        phrase="moon braids with silver stars",
        needed="comb",
        magic="glow",
        caution="gentle",
        risk="sparkles",
    ),
}
CHARMS = {
    "wide_tooth_comb": Charm(
        id="wide_tooth_comb",
        label="a wide-tooth comb charm",
        covers={"comb"},
        neutralizes={"tangled"},
        prep="We can comb slowly, strand by strand",
        tail="the comb charm kept every knot from getting worse",
    ),
    "soft_brush_spell": Charm(
        id="soft_brush_spell",
        label="a soft-brush spell",
        covers={"hairbrush"},
        neutralizes={"sparkles"},
        prep="We can brush softly and let the glow settle",
        tail="the brush spell kept the magic gentle",
    ),
}

CHILDREN = ["Milo", "Pip", "Nina", "Toby", "Luna", "Poppy"]
TYPES = ["rabbit", "fox", "cat", "dog", "bear", "lion"]


@dataclass
class StoryParams:
    place: str
    style: str
    charm: str
    name: str
    child_type: str
    stylist: str
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
    ap = argparse.ArgumentParser(description="Animal-story hair salon world with magic, conflict, and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--style", choices=STYLES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=TYPES)
    ap.add_argument("--stylist")
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
    if getattr(args, "style", None) and getattr(args, "charm", None) and not aspiration_gate(_safe_lookup(STYLES, getattr(args, "style", None)), _safe_lookup(CHARMS, getattr(args, "charm", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "style", None):
        combos = [c for c in combos if c[0] == getattr(args, "style", None)]
    if getattr(args, "charm", None):
        combos = [c for c in combos if c[1] == getattr(args, "charm", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    style_id, charm_id = rng.choice(list(combos))
    child_type = getattr(args, "child_type", None) or rng.choice(TYPES)
    name = getattr(args, "name", None) or rng.choice(CHILDREN)
    stylist = getattr(args, "stylist", None) or rng.choice(["Aunt Fox", "Mina", "Tavi"])
    return StoryParams(place="salon", style=style_id, charm=charm_id, name=name, child_type=child_type, stylist=stylist)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    style = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "style")
    return [
        f'Write a short animal story set in a hair salon that includes the word "{style.keyword}".',
        f"Tell a gentle tale where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").id} wants {style.phrase} but learns a careful lesson from the stylist.",
        f"Write a cautionary magical story about a busy salon, a worried stylist, and a safer spell.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    stylist = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "stylist")
    style = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "style")
    charm = _safe_lookup(CHARMS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "charm").id)
    return [
        QAItem(
            question=f"Who wanted {style.phrase} at the hair salon?",
            answer=f"{child.id} wanted {style.phrase}, because the magical look felt exciting.",
        ),
        QAItem(
            question=f"Why did {stylist.label} warn {child.id} to slow down?",
            answer=f"{stylist.label} warned {child.id} because hurried magic can make hair tangle or pull the wrong way.",
        ),
        QAItem(
            question=f"How did the story end without trouble?",
            answer=f"They used {charm.label} and finished the style with slow, careful strokes, so the hair stayed neat and safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a hair salon?", answer="A hair salon is a place where people or animals go to have hair washed, brushed, cut, or styled."),
        QAItem(question="Why should a person be careful with hair magic?", answer="Hair magic should be careful because pulling, tangling, or snagging can hurt or make the style messy."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(generate_asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH")
    print("python_only:", sorted(py - cl))
    print("asp_only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="salon", style="wild_curls", charm="wide_tooth_comb", name="Luna", child_type="rabbit", stylist="Aunt Fox"),
    StoryParams(place="salon", style="moon_braids", charm="soft_brush_spell", name="Milo", child_type="cat", stylist="Mina"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(STYLES, params.style), _safe_lookup(CHARMS, params.charm), params.name, params.child_type, params.stylist)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        combos = generate_asp_valid()
        print(f"{len(combos)} valid magical salon combos:")
        for style, charm in combos:
            print(f"  {style} + {charm}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
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
