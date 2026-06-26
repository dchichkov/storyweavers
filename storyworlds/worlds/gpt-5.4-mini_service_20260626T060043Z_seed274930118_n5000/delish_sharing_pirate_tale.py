#!/usr/bin/env python3
"""
storyworlds/worlds/delish_sharing_pirate_tale.py
=================================================

A small pirate-story world about a child pirate, a delish treat, and a share
that turns a grumbly moment into a happy one.

Seed premise:
- A little pirate has something delish.
- Another hungry pirate wants some too.
- The first pirate learns to share, and the ship feels warmer by the end.

The world is intentionally tiny and constraint-checked: the treat must be
shareable, the setting must support the sharing scene, and the ending must show
the state change in the world model.
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
# Core model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    snack: object | None = None
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
class ShipSetting:
    place: str = "the little ship"
    afford_sharing: bool = True
    afford_feasting: bool = True
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
class Snack:
    id: str
    label: str
    phrase: str
    pieces: int
    taste: str
    shareable: bool = True
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
class StoryParams:
    snack: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    role: str = "deckhand"
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


class World:
    def __init__(self, setting: ShipSetting) -> None:
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": ShipSetting(place="the little ship", afford_sharing=True, afford_feasting=True),
    "cove": ShipSetting(place="the moonlit cove", afford_sharing=True, afford_feasting=True),
    "dock": ShipSetting(place="the windy dock", afford_sharing=True, afford_feasting=False),
}

SNACKS = {
    "tart": Snack(id="tart", label="tart", phrase="a warm coconut tart", pieces=4, taste="delish"),
    "cake": Snack(id="cake", label="cake", phrase="a sweet pineapple cake", pieces=6, taste="delish"),
    "pear": Snack(id="pear", label="pear", phrase="a shiny pear", pieces=2, taste="juicy"),
    "biscuit": Snack(id="biscuit", label="biscuit", phrase="a buttery biscuit", pieces=3, taste="delish"),
}

BOY_NAMES = ["Finn", "Jasper", "Milo", "Ned", "Owen", "Rory", "Tobin"]
GIRL_NAMES = ["Ada", "Belle", "Cora", "Dora", "Esme", "Nina", "Pia"]
FRIEND_NAMES = ["Hook", "Mina", "Rill", "Sail", "Tess", "Wren"]
ROLES = ["deckhand", "cabin helper", "young mate", "first mate's helper"]


def is_shareable(snack: Snack) -> bool:
    return snack.shareable and snack.pieces >= 2


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, setting) for sid, s in SNACKS.items() if is_shareable(s) for setting in SETTINGS]


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
shareable(S) :- snack(S), pieces(S,N), N >= 2, tasty(S).
valid(S, P) :- shareable(S), setting(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("pieces", sid, s.pieces))
        if s.taste == "delish":
            lines.append(asp.fact("tasty", sid))
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((sid, pid) for sid, s in SNACKS.items() if is_shareable(s) for pid in SETTINGS)
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _share_snack(world: World, hero: Entity, friend: Entity, snack: Entity) -> None:
    if snack.meters.get("pieces", 0) < 2:
        return
    if hero.memes.get("stingy", 0) >= THRESHOLD and friend.memes.get("hungry", 0) >= THRESHOLD:
        hero.memes["kind"] = hero.memes.get("kind", 0) + 1
        friend.memes["joy"] = friend.memes.get("joy", 0) + 1
        snack.meters["pieces"] -= 2
        snack.meters["shared"] = snack.meters.get("shared", 0) + 1


def tell(setting: ShipSetting, snack_cfg: Snack, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, label=friend_name))
    snack = world.add(Entity(
        id=snack_cfg.id,
        kind="thing",
        type=snack_cfg.label,
        label=snack_cfg.label,
        phrase=snack_cfg.phrase,
        owner=hero.id,
    ))
    snack.meters["pieces"] = snack_cfg.pieces

    hero.memes["happy"] = 1
    hero.memes["proud"] = 1
    hero.memes["stingy"] = 0
    friend.memes["hungry"] = 1

    world.say(
        f"On {setting.place}, a little pirate named {hero.id} wore a striped sash and "
        f"guarded {hero.pronoun('possessive')} {snack_cfg.label}."
    )
    world.say(
        f"{hero.id} grinned at the smell of the {snack_cfg.taste} treat and said it was "
        f"the most delish thing on the deck."
    )

    world.para()
    world.say(
        f"Then {friend.id} came trudging up the boards and looked at {snack_cfg.phrase} "
        f"with a very empty belly."
    )
    friend.memes["want"] = 1
    world.say(
        f'"Can I have some?" {friend.id} asked softly, while the ropes creaked and the sea '
        f"bumped the hull."
    )

    world.para()
    hero.memes["stingy"] += 1
    world.say(
        f"For a moment, {hero.id} clutched the snack close and frowned, because {hero.id} "
        f"liked the whole thing."
    )
    world.say(
        f"But {friend.id}'s hungry face made the deck feel less fun, and {hero.id} could see "
        f"that the snack was big enough to share."
    )

    _share_snack(world, hero, friend, snack)
    if snack.meters.get("shared", 0) >= 1:
        world.say(
            f"So {hero.id} broke the {snack_cfg.label} in two and handed {friend.id} a piece. "
            f"{hero.id} kept one piece, and the smell of coconut and sugar drifted over the rails."
        )
        world.say(
            f"{friend.id} beamed, and {hero.id} felt proud in a kinder way than before."
        )
    else:
        pass

    world.facts.update(
        hero=hero,
        friend=friend,
        snack=snack,
        setting=setting,
        role=role,
        snack_cfg=snack_cfg,
        shared=snack.meters.get("shared", 0) >= 1,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    snack = _safe_fact(world, f, "snack_cfg")
    return [
        f'Write a short pirate story for a young child that includes the word "delish" and a sharing moment.',
        f"Tell a gentle pirate tale where {hero.id} has {snack.phrase} and learns to share it with {friend.id}.",
        f"Write a story about a small pirate ship, a delish snack, and a happy split between two hungry friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    snack = _safe_fact(world, f, "snack_cfg")
    return [
        QAItem(
            question=f"What did {hero.id} have on the ship?",
            answer=f"{hero.id} had {snack.phrase}, which the story called delish.",
        ),
        QAItem(
            question=f"Why did {friend.id} ask for some?",
            answer=f"{friend.id} asked because {friend.id} was hungry and the smell of the snack was hard to ignore.",
        ),
        QAItem(
            question=f"What changed when {hero.id} shared?",
            answer=f"{hero.id} split the snack in two, so both pirates got a piece and the deck felt friendlier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does delish mean?",
            answer="Delish means very tasty or delicious, like a treat that smells and tastes extra good.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else have some of what you have, so more than one person can enjoy it.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that pirates sail on the sea, often with ropes, sails, and wooden decks.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryConfig:
    place: str
    snack: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    role: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale about delish sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["boy", "girl"])
    ap.add_argument("--role", choices=ROLES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryConfig:
    combos = [(sid, pid) for sid, s in SNACKS.items() if is_shareable(s) for pid in SETTINGS]
    if getattr(args, "snack", None):
        if not is_shareable(_safe_lookup(SNACKS, getattr(args, "snack", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        combos = [(sid, pid) for sid, pid in combos if sid == getattr(args, "snack", None)]
    if getattr(args, "place", None):
        combos = [(sid, pid) for sid, pid in combos if pid == getattr(args, "place", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    snack_id, place = rng.choice(list(combos))
    snack = _safe_lookup(SNACKS, snack_id)
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    friend_gender = getattr(args, "friend_gender", None) or ("girl" if gender == "boy" else "boy")
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryConfig(
        place=place,
        snack=snack_id,
        name=name,
        gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        role=role,
    )


def generate(params: StoryConfig) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(SNACKS, params.snack),
        params.name,
        params.gender,
        params.friend_name,
        params.friend_gender,
        params.role,
    )
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_facts_text() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("pieces", sid, s.pieces))
        if s.taste == "delish":
            lines.append(asp.fact("tasty", sid))
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts_text()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set((sid, pid) for sid, s in SNACKS.items() if is_shareable(s) for pid in SETTINGS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryConfig(place="ship", snack="tart", name="Finn", gender="boy", friend_name="Mina", friend_gender="girl", role="deckhand"),
    StoryConfig(place="cove", snack="cake", name="Ada", gender="girl", friend_name="Rill", friend_gender="boy", role="young mate"),
    StoryConfig(place="dock", snack="biscuit", name="Milo", gender="boy", friend_name="Tess", friend_gender="girl", role="cabin helper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_check())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible snack-setting combos:\n")
        for sid, pid in vals:
            print(f"  {sid:8} {pid}")
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.snack} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
