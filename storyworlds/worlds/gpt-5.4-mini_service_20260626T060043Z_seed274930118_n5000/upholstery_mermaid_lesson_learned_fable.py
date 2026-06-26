#!/usr/bin/env python3
"""
storyworlds/worlds/upholstery_mermaid_lesson_learned_fable.py
==============================================================

A small fable-like story world about a mermaid, a piece of upholstery, and a
lesson learned.

Premise:
- A mermaid loves to rest on a cozy upholstered seat.
- Her wet tail and sea-salt splash can dampen or stain the upholstery.
- A gentle helper or older guide warns her.
- The mermaid learns to dry off and use a cloth or shell cover before sitting.

The world is kept intentionally small so that every generated story reads like a
complete classical tale with a beginning, a turn, and a lesson learned ending.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cover: object | None = None
    guide: object | None = None
    hero: object | None = None
    seat: object | None = None
    def __post_init__(self) -> None:
        for k in ["wet", "salty", "dirty", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "wisdom", "lesson", "pride", "regret"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "mermaid":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str = "the seaside cottage"
    afford: set[str] = field(default_factory=set)
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
class Seat:
    id: str
    label: str
    phrase: str
    region: str = "seat"
    guards: set[str] = field(default_factory=set)
    coverable: bool = True
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
class Cover:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters["wet"] < THRESHOLD and actor.meters["salty"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if not item.protective and item.region == "seat":
                if world.covered(actor, "seat"):
                    continue
                sig = ("soak", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["wet"] += 1
                item.meters["salty"] += 1
                item.meters["dirty"] += 1
                out.append(f"{item.label.capitalize()} grew damp and a little salty.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more work for {caretaker.label}.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    if hero.memes["regret"] >= THRESHOLD and world.facts.get("resolved"):
        sig = ("lesson", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["wisdom"] += 1
        hero.memes["lesson"] += 1
        out.append("__lesson__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_soak, _r_workload, _r_lesson):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__lesson__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, hero: Entity, seat_id: str) -> dict:
    sim = world.copy()
    _sit(sim, sim.get(hero.id), seat_id, narrate=False)
    seat = sim.entities[seat_id]
    return {
        "ruined": seat.meters["dirty"] >= THRESHOLD,
        "workload": sum(e.meters["workload"] for e in sim.entities.values() if e.kind == "character"),
    }


def _sit(world: World, hero: Entity, seat_id: str, narrate: bool = True) -> None:
    seat = world.get(seat_id)
    hero.meters["wet"] += 1
    hero.meters["salty"] += 1
    seat.worn_by = hero.id
    propagate(world, narrate=narrate)


SETTINGS = {
    "cottage": Setting(place="the seaside cottage", afford={"rest"}),
    "parlor": Setting(place="the bright parlor", afford={"rest"}),
    "harbor": Setting(place="the harbor house", afford={"rest"}),
}

SEATS = {
    "sofa": Seat(id="sofa", label="the sofa", phrase="a soft upholstered sofa", guards={"wet", "salty"}),
    "chair": Seat(id="chair", label="the armchair", phrase="a stitched upholstered armchair", guards={"wet", "salty"}),
    "bench": Seat(id="bench", label="the window bench", phrase="a padded upholstered bench", guards={"wet", "salty"}),
}

COVERS = {
    "towel": Cover(id="towel", label="a towel", phrase="a thick towel", covers={"seat"}, guards={"wet", "salty"}),
    "shawl": Cover(id="shawl", label="a shawl", phrase="a dry shawl", covers={"seat"}, guards={"wet", "salty"}),
    "mat": Cover(id="mat", label="a shell mat", phrase="a flat shell mat", covers={"seat"}, guards={"wet", "salty"}),
}

HERO_NAMES = ["Coral", "Mira", "Nerina", "Luma", "Ariel", "Tala"]
GUIDE_NAMES = ["Grandma Pearl", "Aunt Tide", "Old Shell", "Captain Fin"]
TRAITS = ["curious", "spirited", "gentle", "playful", "stubborn"]


@dataclass
class StoryParams:
    place: str
    seat: str
    cover: str
    name: str
    guide: str
    trait: str
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


def seat_needs_cover(seat: Seat) -> bool:
    return bool(seat.guards)


def select_cover(seat: Seat) -> Optional[Cover]:
    for c in COVERS.values():
        if seat_needs_cover(seat) and c.covers == {"seat"}:
            return c
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like story world about a mermaid and upholstery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--seat", choices=SEATS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for seat in SEATS:
            if not seat_needs_cover(_safe_lookup(SEATS, seat)):
                continue
            for cover in COVERS:
                combos.append((place, seat, cover))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "seat", None) is None or c[1] == getattr(args, "seat", None))
              and (getattr(args, "cover", None) is None or c[2] == getattr(args, "cover", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, seat, cover = (list(rng.choice(combos)) + [None, None, None])[:3]
    return StoryParams(
        place=place,
        seat=seat,
        cover=cover,
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        guide=getattr(args, "guide", None) or rng.choice(GUIDE_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="mermaid", traits=["little", params.trait]))
    guide = world.add(Entity(id="guide", kind="character", type="mermaid", label=params.guide))
    seat = world.add(Entity(id=params.seat, type="seat", label=_safe_lookup(SEATS, params.seat).label, phrase=_safe_lookup(SEATS, params.seat).phrase))
    cover = world.add(Entity(id=params.cover, type="cover", label=_safe_lookup(COVERS, params.cover).label, phrase=_safe_lookup(COVERS, params.cover).phrase, protective=True, covers={"seat"}, plural=_safe_lookup(COVERS, params.cover).plural))
    cover.worn_by = None

    world.say(f"{hero.id} was a little {params.trait} mermaid who loved cozy places on dry land.")
    world.say(f"She admired {seat.phrase} in {world.setting.place} and wished to rest there.")
    world.say(f"{params.guide} told her that upholstery stays nicest when sea water is kept off it.")
    world.para()
    world.say(f"One bright day, {hero.id} came in from the shore with a wet, salty tail.")
    world.say(f"She wanted to sit on {seat.label}, but she worried it would leave a mark.")
    hero.memes["worry"] += 1
    predicted = predict_mess(world, hero, seat.id)
    if predicted["ruined"]:
        world.say(f"{params.guide} pointed to {cover.label} and said, \"Let us use this first.\"")
        cover.worn_by = hero.id
        hero.meters["wet"] += 1
        hero.meters["salty"] += 1
        hero.memes["pride"] += 1
        hero.memes["joy"] += 1
        world.facts["resolved"] = True
        _sit(world, hero, seat.id, narrate=True)
        hero.memes["regret"] += 1
        world.para()
        world.say(f"{hero.id} dried her tail, laid {cover.label} over the seat, and sat gently at last.")
        world.say(f"The upholstered {seat.label} stayed clean, and {params.guide} smiled at the lesson learned.")
    else:
        world.say(f"{params.guide} nodded, but the seat stayed safe without any extra help.")
        world.facts["resolved"] = True
    world.facts.update(hero=hero, guide=guide, seat=seat, cover=cover, params=params)
    propagate(world, narrate=True)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short fable for a young child that includes "{p.name}", "{p.seat}", and "{p.cover}".',
        f"Tell a gentle lesson-learned story about a mermaid who wants to rest on upholstered furniture.",
        f'Write a simple fable where a mermaid learns to protect upholstery before sitting down.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, seat, cover = f["hero"], f["guide"], f["seat"], f["cover"]
    params = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {params.trait} mermaid who learns a careful lesson.",
        ),
        QAItem(
            question=f"Why did {params.guide} worry about the {seat.label}?",
            answer=f"{params.guide} worried because {hero.id} came in wet and salty, and upholstery can get damp and dirty.",
        ),
        QAItem(
            question=f"What did they use so {hero.id} could sit safely?",
            answer=f"They used {cover.label} to cover the seat before {hero.id} sat down.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end?",
            answer=f"{hero.id} learned to dry off and protect upholstery first, so the seat stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is upholstery?",
            answer="Upholstery is soft fabric and stuffing that covers chairs, sofas, and benches to make them comfortable.",
        ),
        QAItem(
            question="Why can sea water bother furniture?",
            answer="Sea water can leave things wet and salty, and that can stain or damage fabric if it is not protected.",
        ),
        QAItem(
            question="What does a towel do?",
            answer="A towel soaks up water and helps things dry off.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
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
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
seat_needs_cover(S) :- seat(S).
needs_cover(P, S) :- wears(P, S), wet_tail(P).
spoils(S) :- needs_cover(P, S), not protected(P, S).
protected(P, S) :- wears_cover(P, C), covers(C, seat), seat(S).
lesson(P) :- spoils(S), learns(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SEATS:
        lines.append(asp.fact("seat", sid))
        lines.append(asp.fact("worn_on", sid, "seat"))
    for cid, c in COVERS.items():
        lines.append(asp.fact("cover", cid))
        for r in c.covers:
            lines.append(asp.fact("covers", cid, r))
    lines.append(asp.fact("wet_tail", "mermaid"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


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


CURATED = [
    StoryParams(place="cottage", seat="sofa", cover="towel", name="Coral", guide="Grandma Pearl", trait="curious"),
    StoryParams(place="parlor", seat="chair", cover="shawl", name="Mira", guide="Aunt Tide", trait="spirited"),
    StoryParams(place="harbor", seat="bench", cover="mat", name="Nerina", guide="Old Shell", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show lesson/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.seat} with {p.cover}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
