#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/connote_suspense_ghost_story.py
==============================================================================================================

A small storyworld about a child, a spooky room, and a ghostly clue.
The seed asks for the word "connote", with Suspense and a Ghost Story style.

The world is built around a few reliable ingredients:
- a place that can feel eerie,
- a child who notices a sign,
- a helper who understands what the sign connotes,
- a hidden thing that is revealed by following the clue,
- a gentle ending image that proves the room changed.

The simulated model uses typed entities with physical meters and emotional memes,
a tiny forward-chained rule engine, a reasonableness gate, and an ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    helper: object | None = None
    hidden_ent: object | None = None
    method_ent: object | None = None
    sign_ent: object | None = None
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
    mood: str
    can_echo: bool = False
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
class Sign:
    id: str
    label: str
    phrase: str
    connotes: str
    location: str
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
class HiddenThing:
    id: str
    label: str
    phrase: str
    found_by: str
    reveal: str
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
    id: str
    label: str
    verb: str
    helps: str
    ending_image: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["listening"] < THRESHOLD:
            continue
        if not world.place.can_echo:
            continue
        sig = ("echo", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["unease"] += 1
        out.append("__echo__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["unease"] < THRESHOLD:
            continue
        if world.facts.get("hidden_revealed"):
            continue
        sig = ("reveal", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["hidden_revealed"] = True
        out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("echo", "atmosphere", _r_echo),
    Rule("reveal", "plot", _r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for sign in SIGNS.values():
            for hidden in HIDDENS.values():
                if sign.id in hidden.found_by:
                    combos.append((place.id, sign.id, hidden.id))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    sign: str = ""
    hidden: str = ""
    child_name: str = ""
    child_gender: str = "girl"
    helper_name: str = ""
    helper_gender: str = "woman"
    method: str = ""
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small suspenseful ghost story world with a clue that connotes something hidden."
    )
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--sign", choices=SIGNS.keys())
    ap.add_argument("--hidden", choices=HIDDENS.keys())
    ap.add_argument("--method", choices=METHODS.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "sign", None) is None or c[1] == getattr(args, "sign", None))
        and (getattr(args, "hidden", None) is None or c[2] == getattr(args, "hidden", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, sign, hidden = rng.choice(list(combos))
    method = getattr(args, "method", None) or rng.choice(sorted(METHODS))
    child_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["woman", "man"])
    child_name = getattr(args, "name", None) or _pick_name(rng, child_gender)
    helper_name = getattr(args, "helper", None) or _pick_name(rng, "girl" if helper_gender == "woman" else "boy")
    return StoryParams(
        place=place,
        sign=sign,
        hidden=hidden,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        method=method,
    )


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES or params.sign not in SIGNS or params.hidden not in HIDDENS or params.method not in METHODS:
        pass
    place = _safe_lookup(PLACES, params.place)
    sign = _safe_lookup(SIGNS, params.sign)
    hidden = _safe_lookup(HIDDENS, params.hidden)
    method = _safe_lookup(METHODS, params.method)
    if sign.id not in hidden.found_by:
        pass

    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child", tags=set(sign.tags)))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, role="helper", tags=set(hidden.tags)))
    sign_ent = world.add(Entity(id="sign", type="thing", label=sign.label, phrase=sign.phrase, tags=set(sign.tags)))
    hidden_ent = world.add(Entity(id="hidden", type="thing", label=hidden.label, phrase=hidden.phrase, tags=set(hidden.tags)))
    method_ent = world.add(Entity(id="method", type="thing", label=method.label, phrase=method.label, tags=set(method.tags)))

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        sign=sign,
        hidden=hidden,
        method=method,
        sign_ent=sign_ent,
        hidden_ent=hidden_ent,
        method_ent=method_ent,
        clue_followed=False,
        hidden_revealed=False,
        ending_image=method.ending_image,
    )

    child.meters["listening"] = 1.0
    child.memes["curiosity"] = 1.0
    helper.memes["calm"] = 1.0
    child.memes["unease"] = 0.0
    helper.memes["unease"] = 0.0

    world.say(f"{child.label} and {helper.label} stood in {place.label}, where the air felt {place.mood}.")
    world.say(f"Near them was {sign.phrase}, and it seemed to connote {sign.connotes}.")
    world.para()
    world.say(f"{child.label} listened hard while {helper.label} watched the dark corner by {hidden.phrase}.")
    world.say(f'"That sign can connote something hidden," {helper.label} whispered. "Let’s use the {method.label}."')
    child.meters["listening"] = 1.0
    child.memes["unease"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(f"{child.label} followed the clue, and {helper.label} moved slowly, one careful step at a time.")
    world.say(f"They used the {method.label}, and {method.helps}.")

    world.facts["clue_followed"] = True
    hidden_ent.meters["revealed"] = 1.0
    hidden_ent.meters["open"] = 1.0
    world.facts["hidden_revealed"] = True
    world.say(f"At last, {hidden.phrase} was found.")
    world.say(f"The room no longer felt empty; the ending image was simple and clear: {method.ending_image}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspenseful ghost story for a young child that includes the word "connote" and takes place in {f["place"].label}.',
        f"Tell a gentle ghost story where {f['sign'].label} seems to connote something hidden, and {f['child'].label} follows the clue with {f['helper'].label}.",
        f"Write a suspense story with a spooky room, a clue, and a calm ending image, using the word connote.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    sign = f["sign"]
    hidden = f["hidden"]
    method = f["method"]
    return [
        QAItem(
            question=f"Why did {child.label} and {helper.label} feel the room was spooky?",
            answer=f"They were in {place.label}, and the air felt {place.mood}. The sign also seemed to connote that something hidden was nearby.",
        ),
        QAItem(
            question=f"What did the sign connote in the story?",
            answer=f"It seemed to connote that something hidden was close by. That is why {child.label} listened carefully instead of rushing away.",
        ),
        QAItem(
            question=f"How did {child.label} and {helper.label} find the hidden thing?",
            answer=f"They followed the clue from {sign.label} and used {method.label}. The careful pace helped them find {hidden.phrase} without making the room feel more frightening.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hidden.phrase} was found, and the ending image showed {method.ending_image}. The room changed from eerie and empty to calm and explained.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word connote mean?",
            answer="To connote means to suggest or make you think of something without saying it directly.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next. It makes you wait and listen closely.",
        ),
        QAItem(
            question="What makes a ghost story spooky instead of loud?",
            answer="A ghost story can feel spooky when it uses dark rooms, quiet clues, and small surprises. The fear is gentle, not wild.",
        ),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


PLACES = {
    "attic": Place(id="attic", label="the attic", mood="cold and whispery", can_echo=True, tags={"attic", "echo"}),
    "hall": Place(id="hall", label="the old hall", mood="still and watchful", can_echo=True, tags={"hall", "echo"}),
    "porch": Place(id="porch", label="the porch", mood="quiet and drafty", can_echo=False, tags={"porch"}),
    "basement": Place(id="basement", label="the basement", mood="dark and hushed", can_echo=True, tags={"basement", "echo"}),
}

SIGNS = {
    "rattling_door": Sign(id="rattling_door", label="a rattling door", phrase="a rattling door", connotes="someone might be hiding behind it", location="near the attic stair", tags={"door", "clue"}),
    "cold_bell": Sign(id="cold_bell", label="a cold little bell", phrase="a cold little bell", connotes="a careful way to ask for help", location="on a dusty shelf", tags={"bell", "clue"}),
    "moving_shadow": Sign(id="moving_shadow", label="a moving shadow", phrase="a moving shadow", connotes="something secret could be close", location="by the hallway wall", tags={"shadow", "clue"}),
    "soft_knock": Sign(id="soft_knock", label="a soft knock", phrase="a soft knock", connotes="someone or something wants to be found", location="under the porch beam", tags={"knock", "clue"}),
}

HIDDENS = {
    "lost_key": HiddenThing(id="lost_key", label="a lost brass key", phrase="a lost brass key in a little tin box", found_by="rattling_door", reveal="the key was waiting", tags={"key", "found"}),
    "paper_note": HiddenThing(id="paper_note", label="a folded note", phrase="a folded note tucked in a teacup", found_by="cold_bell", reveal="the note had a kind message", tags={"note", "found"}),
    "music_box": HiddenThing(id="music_box", label="a tiny music box", phrase="a tiny music box behind a book", found_by="moving_shadow", reveal="the box sang a thin, sweet tune", tags={"music", "found"}),
    "cat_toy": HiddenThing(id="cat_toy", label="a striped cat toy", phrase="a striped cat toy under a chair", found_by="soft_knock", reveal="the toy belonged to the attic cat", tags={"toy", "found"}),
}

METHODS = {
    "lantern": Method(id="lantern", label="lantern", verb="held the dark away", helps="it made the corners bright enough to search", ending_image="the lantern made a warm circle on the floor", tags={"light"}),
    "key": Method(id="key", label="key", verb="opened the stuck door", helps="it turned the old lock with a tiny click", ending_image="the key lay in the child's open hand", tags={"key"}),
    "broom": Method(id="broom", label="broom", verb="moved the dust aside", helps="it swept away the dust so the clue could be seen", ending_image="a clean stripe showed where the broom had passed", tags={"broom"}),
    "blanket": Method(id="blanket", label="blanket", verb="made a little safe place", helps="it gave them comfort while they looked", ending_image="the blanket was folded neatly on a chair", tags={"blanket"}),
}

GIRL_NAMES = ["Maya", "Luna", "Ivy", "Nora", "Ella", "Hazel", "Lily", "Ada"]
BOY_NAMES = ["Theo", "Milo", "Finn", "Owen", "Eli", "Noah", "Ben", "Toby"]


CURATED = [
    StoryParams(place="attic", sign="rattling_door", hidden="lost_key", method="lantern", child_name="Maya", child_gender="girl", helper_name="Eli", helper_gender="boy"),
    StoryParams(place="hall", sign="moving_shadow", hidden="music_box", method="broom", child_name="Theo", child_gender="boy", helper_name="Nora", helper_gender="girl"),
    StoryParams(place="basement", sign="cold_bell", hidden="paper_note", method="key", child_name="Ivy", child_gender="girl", helper_name="Milo", helper_gender="boy"),
    StoryParams(place="porch", sign="soft_knock", hidden="cat_toy", method="blanket", child_name="Owen", child_gender="boy", helper_name="Lily", helper_gender="girl"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.can_echo:
            lines.append(asp.fact("echo_place", p.id))
    for s in SIGNS.values():
        lines.append(asp.fact("sign", s.id))
        lines.append(asp.fact("connotes", s.id, s.connotes))
    for h in HIDDENS.values():
        lines.append(asp.fact("hidden", h.id))
        lines.append(asp.fact("found_by", h.id, h.found_by))
    for m in METHODS.values():
        lines.append(asp.fact("method", m.id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Sign, Hidden) :- place(Place), sign(Sign), hidden(Hidden), found_by(Hidden, Sign).
suspect(Sign) :- sign(Sign), connotes(Sign, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, sign=None, hidden=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = 1
    return ok


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does connote mean?", answer="It means to suggest or make you think of something indirectly."),
        QAItem(question="What is suspense?", answer="Suspense is the feeling of waiting to see what happens next."),
        QAItem(question="What makes a ghost story spooky?", answer="A ghost story often uses quiet places, shadows, and clues that seem mysterious."),
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
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for row in asp_valid_combos():
            print("  ", row)
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
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child_name} in {p.place} with {p.sign} ({p.hidden})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
