#!/usr/bin/env python3
"""
storyworlds/worlds/granny_confidante_lesson_learned_twist_folk_tale.py
======================================================================

A small folk-tale story world about a granny, a confidante, and a lesson
learned with a gentle twist.

Premise:
- Granny prepares a small gift for the village.
- Her confidante notices a problem on the path.
- They face a folk-tale twist: the feared troublemaker is not what it seemed.
- The lesson learned is that wise listening and kind caution can reveal the
  right path.

The world simulates:
- physical state in meters (distance, damage, hunger, dryness, warmth)
- emotional state in memes (trust, worry, courage, relief, pride)

The narration is state-driven: the story changes because the simulated world
changes.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    confidante: object | None = None
    gift_ent: object | None = None
    granny: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"granny", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "father", "boy"}:
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
    place: str = "the village lane"
    weather: str = "misty"
    affords: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    verb: str
    gerund: str
    risk: str
    keyword: str
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
class Gift:
    label: str
    phrase: str
    region: str
    fragile: bool = True
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
class Twist:
    fear_name: str
    reveal_name: str
    reveal_kind: str
    lesson: str
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
class StoryParams:
    setting: str = ""
    goal: str = ""
    gift: str = ""
    granny_name: str = ""
    confidante_name: str = ""
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_blocked: bool = False
        self.twist_seen: bool = False

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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def _mget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meget(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _setm(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = _mget(ent, key) + delta


def _sete(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = _meget(ent, key) + delta


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    granny = world.get("granny")
    conf = world.get("confidante")
    if world.path_blocked and _meget(granny, "worry") < THRESHOLD:
        _sete(granny, "worry", 1)
        _sete(conf, "worry", 1)
        out.append(f"{granny.id} felt a pinch of worry, and {conf.id} felt it too.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    granny = world.get("granny")
    conf = world.get("confidante")
    if world.twist_seen and _meget(granny, "relief") < THRESHOLD:
        _sete(granny, "relief", 1)
        _sete(conf, "relief", 1)
        out.append(f"Their worry melted into relief.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_worry, _r_relief):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def encounter_blockage(world: World) -> None:
    world.path_blocked = True
    world.get("granny").meters["distance"] += 0.2
    world.get("confidante").memes["alert"] = 1


def reveal_twist(world: World) -> None:
    world.twist_seen = True
    world.path_blocked = False


SETTING_REGISTRY = {
    "village": Setting(place="the village lane", weather="misty", affords={"walk"}),
    "wood": Setting(place="the mossy wood", weather="foggy", affords={"walk"}),
    "river": Setting(place="the river path", weather="blowy", affords={"walk"}),
}

GOAL_REGISTRY = {
    "honey": Goal(
        id="honey",
        verb="take honey cakes to the market",
        gerund="carrying honey cakes",
        risk="the cakes might get ruined",
        keyword="honey",
        tags={"sweet", "basket"},
    ),
    "lantern": Goal(
        id="lantern",
        verb="bring a lantern to the chapel",
        gerund="holding a lantern",
        risk="the flame might go out",
        keyword="lantern",
        tags={"light", "night"},
    ),
    "berries": Goal(
        id="berries",
        verb="deliver berries to the miller",
        gerund="carrying berries",
        risk="the berries might be spilled",
        keyword="berries",
        tags={"basket", "wood"},
    ),
}

GIFT_REGISTRY = {
    "cakes": Gift(label="honey cakes", phrase="warm honey cakes", region="hands", fragile=True),
    "lantern": Gift(label="lantern", phrase="a little brass lantern", region="hands", fragile=True),
    "berries": Gift(label="basket", phrase="a basket of red berries", region="hands", fragile=True),
}

TWIST_REGISTRY = {
    "owl": Twist(
        fear_name="night watcher",
        reveal_name="old owl",
        reveal_kind="owl",
        lesson="Not every shadow is a threat; sometimes it is a helper in disguise.",
    ),
    "dog": Twist(
        fear_name="forest thief",
        reveal_name="lost dog",
        reveal_kind="dog",
        lesson="A gentle voice can turn fear into friendship.",
    ),
}

NAMES = [
    "Mabel", "Iris", "Nell", "Bess", "Edna", "June", "Pearl", "Marla", "Tess", "Rose",
    "Otis", "Hugh", "Evan", "Lars", "Jude", "Miles",
]


@dataclass
class StoryWorldState:
    world: World
    granny: Entity
    confidante: Entity
    goal: Goal
    gift: Gift
    twist: Twist
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


ASP_RULES = r"""
setting(village).
setting(wood).
setting(river).
goal(honey).
goal(lantern).
goal(berries).
gift(cakes).
gift(lantern).
gift(berries).

compatible(village,honey,cakes).
compatible(wood,berries,berries).
compatible(river,lantern,lantern).

show_story(S,G,F) :- setting(S), goal(G), gift(F), compatible(S,G,F).
#show show_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for gid in GOAL_REGISTRY:
        lines.append(asp.fact("goal", gid))
    for fid in GIFT_REGISTRY:
        lines.append(asp.fact("gift", fid))
    for sid, setting in SETTING_REGISTRY.items():
        for goal_id in setting.affords:
            lines.append(asp.fact("affords", sid, goal_id))
    for goal_id, goal in GOAL_REGISTRY.items():
        lines.append(asp.fact("goal_verb", goal_id, goal.verb))
        lines.append(asp.fact("goal_risk", goal_id, goal.risk))
    for gift_id, gift in GIFT_REGISTRY.items():
        lines.append(asp.fact("gift_region", gift_id, gift.region))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def story_setup(rng: random.Random, params: StoryParams) -> StoryWorldState:
    setting = _safe_lookup(SETTING_REGISTRY, params.setting)
    goal = _safe_lookup(GOAL_REGISTRY, params.goal)
    gift = _safe_lookup(GIFT_REGISTRY, params.gift)
    twist = rng.choice(list(TWIST_REGISTRY.values()))
    world = World(setting)
    granny = world.add(Entity(
        id="granny",
        kind="character",
        type="granny",
        label=params.granny_name,
        meters={"distance": 0.0, "load": 0.0},
        memes={"care": 1.0, "calm": 1.0, "worry": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    confidante = world.add(Entity(
        id="confidante",
        kind="character",
        type="child",
        label=params.confidante_name,
        meters={"distance": 0.0},
        memes={"trust": 1.0, "alert": 0.0, "worry": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    gift_ent = world.add(Entity(
        id="gift",
        kind="thing",
        type=gift.label,
        label=gift.label,
        phrase=gift.phrase,
        owner="granny",
        caretaker="granny",
        meters={"freshness": 1.0, "damage": 0.0},
    ))
    world.facts.update(granny=granny, confidante=confidante, goal=goal, gift=gift, twist=twist, gift_ent=gift_ent)
    return StoryWorldState(world, granny, confidante, goal, gift, twist)


def tell_story(state: StoryWorldState) -> None:
    w = state.world
    g = state.granny
    c = state.confidante
    goal = state.goal
    gift = state.gift
    twist = state.twist

    w.say(f"{g.label} was a granny who knew the old lanes and the soft ways of the world.")
    w.say(f"She prepared {gift.phrase} so she could {goal.verb}.")
    w.say(f"By her side walked {c.label}, her trusted confidante, who kept a quiet eye on the path.")

    w.para()
    w.say(f"They set out on {w.setting.place}, where the air was {w.setting.weather} and the stones looked slick.")
    w.get("granny").meters["distance"] += 1.0
    w.get("confidante").meters["distance"] += 1.0
    encounter_blockage(w)
    propagate(w)
    w.say(f"Then they saw a dark shape near the hedge, and the path seemed suddenly narrow.")

    w.para()
    w.say(f"{c.label} whispered that it might be a {twist.fear_name}.")
    _sete(c, "trust", 0.5)
    _sete(g, "worry", 0.5)
    w.say(f"{g.label} held the basket still and listened, because a good granny listens before she leaps.")
    w.say(f"She peered closer, and the twist came clear: it was only a {twist.reveal_name}, small and lost, with soft eyes.")
    reveal_twist(w)
    propagate(w)
    _sete(g, "pride", 1.0)
    _sete(c, "pride", 1.0)

    w.para()
    w.say(f"{g.label} softened her voice and offered a crumb.")
    w.say(f"The {twist.reveal_kind} wagged or blinked or hooted kindly, as if it had been waiting for mercy all along.")
    w.say(f"So {c.label} helped guide the little creature homeward, and {g.label} completed her errand with a lighter heart.")
    w.say(f"The lesson learned was simple: {twist.lesson}")
    w.say(f"By the end, the feared shadow had become a friend, and the path felt bright again.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short folk tale about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "granny").label}, her confidante {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "confidante").label}, and a lesson learned with a twist.",
        f"Tell a gentle story where a granny carries {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gift").phrase} along {world.setting.place} and discovers that fear was mistaken.",
        f"Create a small folk tale with a granny, a confidante, and a surprising reveal that ends in a clear lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    g = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "granny")
    c = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "confidante")
    goal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "goal")
    twist = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist")
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"It was mostly about {g.label}, a granny, and her confidante {c.label}.",
        ),
        QAItem(
            question=f"What was {g.label} trying to do at the start?",
            answer=f"She was trying to {goal.verb}.",
        ),
        QAItem(
            question=f"What did {c.label} first think was hiding on the path?",
            answer=f"{c.label} first thought it might be a {twist.fear_name}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The scary shape was only a {twist.reveal_name}, not a danger after all.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=twist.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a confidante?",
            answer="A confidante is a trusted friend who listens carefully and keeps your worries safe.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a old-fashioned story that often teaches a lesson and may include a surprise or a magical-feeling twist.",
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is the good idea or wisdom the characters understand by the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"path_blocked={world.path_blocked} twist_seen={world.twist_seen}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if not model:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP rules loaded and produced a model.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world with granny, confidante, twist, and lesson learned.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--goal", choices=GOAL_REGISTRY)
    ap.add_argument("--gift", choices=GIFT_REGISTRY)
    ap.add_argument("--granny-name")
    ap.add_argument("--confidante-name")
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


CURATED = [
    StoryParams(setting="village", goal="honey", gift="cakes", granny_name="Mabel", confidante_name="Iris"),
    StoryParams(setting="wood", goal="berries", gift="berries", granny_name="Nell", confidante_name="Otis"),
    StoryParams(setting="river", goal="lantern", gift="lantern", granny_name="Bess", confidante_name="June"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "goal", None) and getattr(args, "goal", None) not in _safe_lookup(SETTING_REGISTRY, getattr(args, "setting", None)).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(list(SETTING_REGISTRY))
    possible_goals = sorted(_safe_lookup(SETTING_REGISTRY, setting).affords)
    goal = getattr(args, "goal", None) or rng.choice(possible_goals)
    gift = getattr(args, "gift", None) or goal
    if gift not in GIFT_REGISTRY:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gift", None) and getattr(args, "gift", None) != goal:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    granny = getattr(args, "granny_name", None) or rng.choice(NAMES[:10])
    confidante = getattr(args, "confidante_name", None) or rng.choice(NAMES)
    if confidante == granny:
        confidante = rng.choice([n for n in NAMES if n != granny])
    return StoryParams(setting=setting, goal=goal, gift=gift, granny_name=granny, confidante_name=confidante)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed or 0)
    state = story_setup(rng, params)
    tell_story(state)
    return StorySample(
        params=params,
        story=state.world.render(),
        prompts=generation_prompts(state.world),
        story_qa=story_qa(state.world),
        world_qa=world_knowledge_qa(state.world),
        world=state.world,
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
