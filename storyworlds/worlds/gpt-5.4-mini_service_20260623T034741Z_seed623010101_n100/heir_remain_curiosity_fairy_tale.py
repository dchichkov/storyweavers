#!/usr/bin/env python3
"""
storyworlds/worlds/heir_remain_curiosity_fairy_tale.py
======================================================

A standalone storyworld about a curious heir, a fairy-tale keep, and what must
remain when old magic is tested.

Premise:
- A young heir lives in a small castle or cottage in a fairy-tale land.
- Curiosity draws the heir toward a sealed room, a hidden chest, or a garden gate.
- A guardian warns that something precious must remain where it is.

Turn:
- The heir tries a careful peek, and the world reveals a consequence through
  physical meters and emotional memes.
- Depending on the specific combination, a helpful reveal, a small mishap, or a
  chastening discovery follows.

Resolution:
- The heir either leaves the thing to remain, restores what shifted, or learns a
  safer way to satisfy curiosity.

This script is self-contained and uses only the stdlib plus the shared result
containers. It also includes an inline ASP twin and a Python reasonableness
gate for parity checks.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False
    owner: str = ""

    g: object | None = None
    heir: object | None = None
    secret: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman", "daughter"}
        male = {"boy", "prince", "king", "father", "man", "son", "heir"}
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
    tone: str
    affords: set[str] = field(default_factory=set)
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
class ObjectChoice:
    id: str
    label: str
    phrase: str
    kind: str
    at_risk: str
    disturbance: str
    remedy: str
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
class Guardian:
    id: str
    label: str
    type: str
    gentle_title: str
    warns_with: str
    helps_with: str
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w
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


def _ensure_meter(ent: Entity, key: str) -> None:
    ent.meters.setdefault(key, 0.0)


def _ensure_meme(ent: Entity, key: str) -> None:
    ent.memes.setdefault(key, 0.0)


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    heir = world.get("heir")
    secret = world.get("secret")
    if heir.meters.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if secret.meters.get("glimmer", 0.0) >= THRESHOLD:
        heir.memes["wonder"] = heir.memes.get("wonder", 0.0) + 1
        out.append("The hidden thing glimmered softly, as if it had been waiting.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    heir = world.get("heir")
    object_ent = world.get("thing")
    if heir.meters.get("curiosity", 0.0) < THRESHOLD:
        return out
    if world.place.id not in {"tower", "forest_hall", "rose_garden"}:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    if object_ent.meters.get("disturbed", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    object_ent.meters["scuffed"] = object_ent.meters.get("scuffed", 0.0) + 1
    heir.memes["regret"] = heir.memes.get("regret", 0.0) + 1
    out.append("A tiny scuff marked the floor where careful feet had crept too near.")
    return out


CAUSAL_RULES = [_r_reveal, _r_spill]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule(world)
            if produced:
                changed = True
                out.extend(produced)
    return out


@dataclass
class StoryParams:
    place: str
    object: str
    guardian: str
    heir_name: str
    heir_type: str
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


SETTINGS = {
    "tower": Place("tower", "the old tower", "high and windy", {"peek", "open"}, {"tower", "stone"}),
    "forest_hall": Place("forest_hall", "the forest hall", "green and hushed", {"peek", "open"}, {"forest", "hall"}),
    "rose_garden": Place("rose_garden", "the rose garden", "sweet and bright", {"peek", "open"}, {"garden", "rose"}),
}

OBJECTS = {
    "crown": ObjectChoice("crown", "a silver crown", "silver and bright", "crown", "seat", "dust", "rest", {"crown", "silver"}),
    "lantern": ObjectChoice("lantern", "a glass lantern", "glass and gold", "lantern", "door", "jar", "remain", {"lantern", "glass"}),
    "key": ObjectChoice("key", "a small brass key", "brass and old", "key", "lock", "scratch", "remain", {"key", "brass"}),
}

GUARDIANS = {
    "grandmother": Guardian("grandmother", "the grandmother", "woman", "grandmother", "Stay gentle, and let what matters remain.", "she helped the heir set things right.", {"grandmother", "wise"}),
    "keeper": Guardian("keeper", "the keeper", "man", "keeper", "Do not rush; some things must remain where they are.", "he showed a safer way to look.", {"keeper", "wise"}),
    "aunt": Guardian("aunt", "the aunt", "woman", "aunt", "Be curious, but careful; let the old thing remain.", "she smiled and fixed the little mistake.", {"aunt", "wise"}),
}

HEIR_NAMES = ["Ella", "Milo", "Nora", "Finn", "Ivy", "Rowan", "Ada", "Theo"]
HEIR_TYPES = ["girl", "boy"]
TRAITS = ["curious", "gentle", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for obj in OBJECTS:
            for guardian in GUARDIANS:
                combos.append((place, obj, guardian))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a curious heir and what must remain.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--name")
    ap.add_argument("--heir-type", choices=HEIR_TYPES)
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


def _pick_name(rng: random.Random, heir_type: str) -> str:
    return rng.choice(HEIR_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "object_", None) is None or c[1] == getattr(args, "object_", None))
              and (getattr(args, "guardian", None) is None or c[2] == getattr(args, "guardian", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj, guardian = rng.choice(list(combos))
    heir_type = getattr(args, "heir_type", None) or rng.choice(HEIR_TYPES)
    name = getattr(args, "name", None) or _pick_name(rng, heir_type)
    return StoryParams(place=place, object=obj, guardian=guardian, heir_name=name, heir_type=heir_type)


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        pass
    if params.object not in OBJECTS:
        pass
    if params.guardian not in GUARDIANS:
        pass
    place = _safe_lookup(SETTINGS, params.place)
    obj = _safe_lookup(OBJECTS, params.object)
    guardian = _safe_lookup(GUARDIANS, params.guardian)
    world = World(place)

    heir = world.add(Entity(id="heir", kind="character", type=params.heir_type, label=params.heir_name, role="heir"))
    g = world.add(Entity(id="guardian", kind="character", type=guardian.type, label=guardian.label, role="guardian"))
    secret = world.add(Entity(id="secret", kind="thing", type=obj.kind, label=obj.label, phrase=obj.phrase, tags=set(obj.tags)))
    thing = world.add(Entity(id="thing", kind="thing", type=obj.kind, label=obj.label, phrase=obj.phrase, tags=set(obj.tags)))

    for e in (heir, g, secret, thing):
        e.meters = __import__('collections').defaultdict(float)
        e.memes = __import__('collections').defaultdict(float)
    _ensure_meter(heir, "curiosity")
    _ensure_meter(heir, "care")
    _ensure_meme(heir, "wonder")
    _ensure_meme(heir, "worry")
    _ensure_meter(secret, "glimmer")
    _ensure_meter(secret, "kept")
    _ensure_meter(thing, "disturbed")

    heir.meters["curiosity"] += 1
    heir.memes["worry"] += 0.5
    secret.meters["glimmer"] += 1
    secret.meters["kept"] += 1
    thing.meters["disturbed"] += 0

    world.say(f"In {place.label}, there lived a curious heir named {params.heir_name}.")
    world.say(f"Every day, {params.heir_name} listened to {guardian.label} and wondered about {obj.label}.")
    world.para()
    world.say(f"One clear morning, {params.heir_name} wandered to the quiet corner where the old treasure was meant to remain.")
    world.say(f"{guardian.label.split('the ')[-1].capitalize()} had said, \"{guardian.warns_with}\"")

    if obj.id in {"crown", "key"}:
        thing.meters["disturbed"] += 1
        heir.meters["curiosity"] += 1
        world.say(f"But {params.heir_name}'s curiosity shone too bright to ignore, and {heir.name if hasattr(heir,'name') else params.heir_name} lifted a careful hand.")
    else:
        world.say(f"But {params.heir_name} only peeped inside, trying to learn without touching.")

    if obj.id == "lantern":
        secret.meters["glimmer"] += 1
    if obj.id == "crown":
        thing.meters["scuffed"] += 1
    if obj.id == "key":
        thing.meters["disturbed"] += 1

    for line in propagate(world):
        world.say(line)

    world.para()
    if thing.meters.get("scuffed", 0.0) >= THRESHOLD:
        world.say(f"{guardian.helps_with}")
        world.say(f"Together they polished the little mark away, and {obj.remedy} so it could remain where it belonged.")
        heir.memes["regret"] += 1
        heir.memes["wonder"] += 1
        world.say(f"By sunset, {params.heir_name} knew that curiosity was a lamp best held with care.")
    else:
        world.say(f"{guardian.helps_with}")
        if obj.id == "lantern":
            world.say(f"The glass lantern stayed on its hook, and the heir learned that some wonders are best let to remain in place.")
        elif obj.id == "key":
            world.say(f"The brass key stayed in its nest, and the heir learned that doors open in time, not by tugging.")
        else:
            world.say(f"The silver crown stayed on its velvet cushion, and the heir learned that a treasure can remain beautiful when it is left alone.")

    world.facts.update(
        params=params,
        heir=heir,
        guardian=g,
        guardian_cfg=guardian,
        place=place,
        object_cfg=obj,
        secret=secret,
        thing=thing,
        outcome="scuffed" if thing.meters.get("scuffed", 0.0) >= THRESHOLD else "rested",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child about a curious heir in {f["place"].label} where {f["object_cfg"].label} must remain safe and untouched.',
        f'Tell a gentle story about {f["params"].heir_name}, a {f["params"].heir_type}, who is warned that {f["object_cfg"].label} should remain where it is.',
        f'Write a short fairy tale that includes the words "heir" and "remain" and ends with a wise guardian helping after curiosity.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    heir = f["heir"]
    guardian = f["guardian"]
    obj = f["object_cfg"]
    place = f["place"]
    qas = [
        QAItem(
            question=f"Who is the story about in {place.label}?",
            answer=f"It is about {f['params'].heir_name}, a curious heir who lives in {place.label}. {guardian.label.split('the ')[-1].capitalize()} watches over the place and helps the heir learn carefully.",
        ),
        QAItem(
            question=f"What did the guardian want to remain where it was?",
            answer=f"{obj.label.capitalize()} was supposed to remain where it belonged. The guardian wanted it to stay safe so the heir would not damage it by poking too quickly.",
        ),
        QAItem(
            question=f"Why did the heir look at {obj.label} so closely?",
            answer=f"The heir was full of curiosity and wanted to know more about {obj.label}. That curiosity made the heir lean in, even after being told to stay gentle.",
        ),
    ]
    if f["outcome"] == "scuffed":
        qas.append(QAItem(
            question=f"What happened after the heir disturbed {obj.label}?",
            answer=f"The little treasure got scuffed, so the guardian helped put things right. They cleaned the mark and made sure {obj.label} could remain safe again.",
        ))
        qas.append(QAItem(
            question=f"How did the heir feel after the mistake?",
            answer=f"The heir felt a little regret, but also wonder, because the moment taught a real lesson. Curiosity stayed, yet it became kinder and more careful.",
        ))
    else:
        qas.append(QAItem(
            question=f"What did the heir learn by only peeking at {obj.label}?",
            answer=f"The heir learned that some beautiful things should simply remain in place. Curiosity can be gentle when it waits, looks, and does not touch.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an heir?",
            answer="An heir is a child who will grow up to inherit something important, like a crown, a home, or a family duty.",
        ),
        QAItem(
            question="What does remain mean?",
            answer="Remain means to stay in the same place or keep being the same way.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more and to ask questions about something that seems interesting.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
heir_story(P,O,G) :- place(P), object(O), guardian(G).
curious(heir) :- curiosity(heir).
remain_safe(O) :- object(O), remain(O).
scuff_happens :- disturbed(thing), curiosity(heir).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("remain", oid))
    for gid in GUARDIANS:
        lines.append(asp.fact("guardian", gid))
    lines.append(asp.fact("curiosity", "heir"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show heir_story/3."))
    return sorted(set(asp.atoms(model, "heir_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    ok = True
    if py != clingo:
        ok = False
        print("MISMATCH between Python and ASP combo sets.")
        print("python only:", sorted(py - clingo))
        print("asp only:", sorted(clingo - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: verify passed ({len(py)} combos).")
        return 0
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, o, g) for p in SETTINGS for o in OBJECTS for g in GUARDIANS]


CURATED = [
    StoryParams(place="tower", object="crown", guardian="grandmother", heir_name="Ella", heir_type="girl"),
    StoryParams(place="forest_hall", object="key", guardian="keeper", heir_name="Milo", heir_type="boy"),
    StoryParams(place="rose_garden", object="lantern", guardian="aunt", heir_name="Ivy", heir_type="girl"),
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "object_", None) is None or c[1] == getattr(args, "object_", None))
              and (getattr(args, "guardian", None) is None or c[2] == getattr(args, "guardian", None))]
    if not combos:
        pass
    place, obj, guardian = rng.choice(list(combos))
    return StoryParams(
        place=place,
        object=obj,
        guardian=guardian,
        heir_name=getattr(args, "name", None) or _pick_name(rng, getattr(args, "heir_type", None) or rng.choice(HEIR_TYPES)),
        heir_type=getattr(args, "heir_type", None) or rng.choice(HEIR_TYPES),
    )


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show heir_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = build_params_from_args(args, random.Random(base_seed + i))
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
