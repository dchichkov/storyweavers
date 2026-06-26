#!/usr/bin/env python3
"""
A tiny fairy-tale story world about a self who learns that curiosity, sharing,
and kindness can open a door in the woods.

The domain is intentionally small: one child-like self, a woodland place, a
few magical objects, and one gentle problem that can be solved by honest
curiosity and kind sharing.
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
# Registry data
# ---------------------------------------------------------------------------

SETTINGS = {
    "glade": {
        "place": "the moonlit glade",
        "light": "silver",
        "magic": "gentle",
        "affords": {"search", "share", "kind"},
    },
    "brook": {
        "place": "the quiet brook",
        "light": "sparkling",
        "magic": "restful",
        "affords": {"search", "share", "kind"},
    },
    "cottage": {
        "place": "the tiny cottage at the edge of the wood",
        "light": "warm",
        "magic": "cozy",
        "affords": {"search", "share", "kind"},
    },
}

GIFTS = {
    "lamp": {
        "label": "a little lantern",
        "phrase": "a little lantern with a round glass belly",
        "type": "lantern",
        "region": "hands",
        "plural": False,
        "genders": {"girl", "boy"},
    },
    "cloak": {
        "label": "a blue cloak",
        "phrase": "a blue cloak stitched with stars",
        "type": "cloak",
        "region": "shoulders",
        "plural": False,
        "genders": {"girl", "boy"},
    },
    "basket": {
        "label": "a berry basket",
        "phrase": "a berry basket woven from reed grass",
        "type": "basket",
        "region": "hands",
        "plural": False,
        "genders": {"girl", "boy"},
    },
}

MAGIC_THINGS = {
    "glowmoss": {
        "label": "glowmoss",
        "phrase": "soft glowmoss under the roots",
        "secret": "it shines brighter when shared",
        "keyword": "glowmoss",
        "tags": {"kind", "share"},
    },
    "starling": {
        "label": "a starling feather",
        "phrase": "a starling feather tucked beneath a stone",
        "secret": "it points the way when a question is asked kindly",
        "keyword": "feather",
        "tags": {"curiosity"},
    },
    "honey": {
        "label": "honey",
        "phrase": "a tiny pot of honey with a wax lid",
        "secret": "it stays sweetest when passed from hand to hand",
        "keyword": "honey",
        "tags": {"share", "kind"},
    },
}

CHAR_NAMES = ["Luna", "Milo", "Iris", "Pip", "Nora", "Theo", "Mira", "Ellis"]
TRAITS = ["curious", "gentle", "brave", "thoughtful", "bright", "patient"]


# ---------------------------------------------------------------------------
# World model
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    planted_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    entities: set[str] = field(default_factory=set)
    gift: object | None = None
    hero: object | None = None
    magic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
    key: str
    place: str
    light: str
    magic: str
    affords: set[str]
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
class Gift:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class MagicThing:
    label: str
    phrase: str
    secret: str
    keyword: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.entities = {k: Entity(**{**v.__dict__, "meters": dict(v.meters), "memes": dict(v.memes)}) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    gift: str
    magic: str
    name: str
    gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
    params: object | None = None
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


def setting_obj(key: str) -> Setting:
    s = _safe_lookup(SETTINGS, key)
    return Setting(key=key, place=s["place"], light=s["light"], magic=s["magic"], affords=set(s["affords"]))


def gift_obj(key: str) -> Gift:
    g = _safe_lookup(GIFTS, key)
    return Gift(label=g["label"], phrase=g["phrase"], type=g["type"], region=g["region"], plural=g["plural"], genders=set(g["genders"]))


def magic_obj(key: str) -> MagicThing:
    m = _safe_lookup(MAGIC_THINGS, key)
    return MagicThing(label=m["label"], phrase=m["phrase"], secret=m["secret"], keyword=m["keyword"], tags=set(m["tags"]))


def build_story(world: World, hero: Entity, gift: Entity, magic: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, there lived a little self named {hero.id}. "
        f"{hero.pronoun().capitalize()} was {hero.traits[0]} and loved to ask questions about every leaf and stone."
    )
    world.say(
        f"One day, {hero.id} carried {gift.phrase} and wandered under the {world.setting.light} trees, "
        f"hoping to discover the secret of {magic.label}."
    )

    world.para()
    world.say(
        f"Near a root, {hero.id} found {magic.phrase}. {hero.pronoun().capitalize()} leaned close and listened. "
        f"{magic.secret.capitalize()}."
    )
    world.say(
        f"{hero.id} felt the first spark of curiosity, but the glimmer was hidden behind a hollow briar."
    )

    world.para()
    world.say(
        f"A little fox with a torn ribbon appeared and looked at the treasure too. "
        f"{hero.id} could keep the hint all to {hero.pronoun('object')}, or {hero.pronoun()} could share."
    )
    world.say(
        f"{hero.id} smiled, held out {gift.it()}, and said, \"We can look together.\" "
        f"That kind choice made the glimmer brighten."
    )
    hero.memes["curiosity"] = 1
    hero.memes["kindness"] = 1
    hero.memes["sharing"] = 1
    magic.meters["glow"] = 1

    world.para()
    world.say(
        f"The fox pointed to a hidden latch, and {hero.id} helped lift it with {gift.label_word}. "
        f"Behind the briar was a tiny path of soft light leading home."
    )
    world.say(
        f"{hero.id} went back with the fox, still carrying {gift.label}, and the secret path stayed bright for both of them."
    )


def generate_world(params: StoryParams) -> World:
    setting = setting_obj(params.setting)
    gift_def = gift_obj(params.gift)
    magic_def = magic_obj(params.magic)

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["curious", "kind"],
        meters={"steps": 1},
        memes={"curiosity": 1, "sharing": 0, "kindness": 0},
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type=gift_def.type,
        label=gift_def.label,
        phrase=gift_def.phrase,
        owner=hero.id,
        carried_by=hero.id,
        region=gift_def.region,
        plural=gift_def.plural,
        meters={"glow": 0},
    ))
    magic = world.add(Entity(
        id="magic",
        kind="thing",
        type=magic_def.keyword,
        label=magic_def.label,
        phrase=magic_def.phrase,
        planted_in=setting.place,
        meters={"glow": 0},
        memes={"mystery": 1},
    ))

    build_story(world, hero, gift, magic)
    world.facts.update(hero=hero, gift=gift, magic=magic, setting=setting, params=params)
    return world


# ---------------------------------------------------------------------------
# Reasonableness and QA
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GIFTS:
            for m in MAGIC_THINGS:
                combos.append((s, g, m))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    gift = _safe_fact(world, f, "gift")
    magic = _safe_fact(world, f, "magic")
    return [
        f'Write a fairy tale about a self named {hero.id} who follows curiosity in {world.setting.place}.',
        f"Tell a gentle story where {hero.id} learns that sharing {gift.label} helps reveal {magic.label}.",
        f'Write a small fairy tale with the words "self", "{magic.keyword}", and "kindness".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    gift = _safe_fact(world, f, "gift")
    magic = _safe_fact(world, f, "magic")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little self named {hero.id} who lives in {setting.place} and follows curiosity.",
        ),
        QAItem(
            question=f"What did {hero.id} carry into the wood?",
            answer=f"{hero.id} carried {gift.phrase} while wandering under the trees.",
        ),
        QAItem(
            question=f"What helped the glimmer get brighter?",
            answer=f"Sharing helped. When {hero.id} shared {gift.label}, the magic of {magic.label} grew brighter.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem at the briar?",
            answer=f"{hero.id} chose kindness and said, \"We can look together,\" so the fox could help open the hidden latch.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to ask questions and learn what is hidden or new.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing is letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle and helpful to others.",
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
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- setting_fact(S).
gift(G) :- gift_fact(G).
magic(M) :- magic_fact(M).

valid_story(S,G,M) :- setting(S), gift(G), magic(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for g in GIFTS:
        lines.append(asp.fact("gift_fact", g))
    for m in MAGIC_THINGS:
        lines.append(asp.fact("magic_fact", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about self, curiosity, sharing, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--magic", choices=MAGIC_THINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    settings = list(SETTINGS)
    gifts = list(GIFTS)
    magics = list(MAGIC_THINGS)

    setting = getattr(args, "setting", None) or rng.choice(settings)
    gift = getattr(args, "gift", None) or rng.choice(gifts)
    magic = getattr(args, "magic", None) or rng.choice(magics)

    if getattr(args, "gift", None) and getattr(args, "gender", None) and getattr(args, "gender", None) not in _safe_lookup(GIFTS, getattr(args, "gift", None))["genders"]:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(GIFTS, gift)["genders"]))
    name = getattr(args, "name", None) or rng.choice(CHAR_NAMES)

    return StoryParams(setting=setting, gift=gift, magic=magic, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.planted_in:
            bits.append(f"planted_in={e.planted_in}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for s, g, m in combos:
            print(f"  {s:8} {g:8} {m:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for s in SETTINGS:
            for g in GIFTS:
                for m in MAGIC_THINGS:
                    params = StoryParams(setting=s, gift=g, magic=m, name="Luna", gender="girl")
                    samples.append(generate(params))
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
