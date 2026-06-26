#!/usr/bin/env python3
"""
storyworlds/worlds/terrific_drink_mammal_foreshadowing_bravery_myth.py
======================================================================

A small myth-style storyworld about a mammal, a terrific drink, an omen,
and a brave choice.

Premise:
- A young mammal is sent to fetch a terrific drink for an elder.
- A foreshadowing sign hints that a difficult path and a fearful choice are
  coming.
- The mammal must decide whether to turn back or continue.

World model:
- Physical meters: thirst, warmth, carrying, spill, storm, tiredness.
- Emotional memes: wonder, worry, bravery, trust, hope.
- A drink can be carried, spilled, shared, or used to restore strength.
- A foreshadowing omen can raise worry before the test arrives.
- Bravery is not the absence of fear; it is the act of moving forward with
  help, purpose, and trust.

This file is standalone and includes:
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- QA generation
- Inline ASP_RULES twin and ASP fact emission
- --verify parity checks
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cup: object | None = None
    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother", "queen"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father", "king"}:
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


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    omen: str = ""
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
class Drink:
    id: str
    label: str
    phrase: str
    taste: str
    warmth: str
    restores: str
    worthy_of: set[str] = field(default_factory=set)
    omen_needed: bool = True
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
class Beast:
    id: str
    type: str
    label: str
    phrase: str
    gender: str
    traits: list[str] = field(default_factory=list)
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
    setting: str
    drink: str
    mammal: str
    name: str
    age: str
    companion: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _apply_omen(world: World) -> list[str]:
    out = []
    if world.facts.get("omen_seen"):
        return out
    world.fired.add(("omen",))
    hero = _safe_fact(world, world.facts, "hero")
    hero.memes["worry"] += 1
    hero.memes["wonder"] += 1
    out.append("At the edge of the road, a sign of trouble shone like a small star before dawn.")
    out.append("The mammal felt the warning in the wind and knew the night would ask for courage.")
    world.facts["omen_seen"] = True
    return out


def _apply_carry(world: World) -> list[str]:
    out = []
    hero = _safe_fact(world, world.facts, "hero")
    drink = _safe_fact(world, world.facts, "drink_ent")
    if hero.id not in world.fired and drink.carried_by == hero.id:
        world.fired.add((hero.id, "carry"))
        hero.meters["carrying"] += 1
        out.append(f"{hero.id} kept the cup steady with careful paws.")
    return out


def _apply_spill(world: World) -> list[str]:
    out = []
    hero = _safe_fact(world, world.facts, "hero")
    drink = _safe_fact(world, world.facts, "drink_ent")
    if hero.meters.get("storm", 0) < THRESHOLD:
        return out
    if drink.carried_by != hero.id:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if world.facts.get("cup_closed"):
        out.append("The lid held fast, and not a single drop escaped.")
        return out
    drink.meters["spill"] = 1
    hero.memes["worry"] += 1
    out.append("A hard gust shook the road, and the drink trembled in the cup.")
    return out


def _apply_bravery(world: World) -> list[str]:
    out = []
    hero = _safe_fact(world, world.facts, "hero")
    if hero.memes.get("worry", 0) < THRESHOLD:
        return out
    if hero.memes.get("bravery", 0) >= THRESHOLD:
        return out
    if world.facts.get("guide") is None:
        return out
    sig = ("brave",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    hero.memes["trust"] += 1
    out.append("Then the remembered words of the elder came back, and fear made room for steady heart.")
    return out


CAUSAL_RULES = [
    _apply_omen,
    _apply_carry,
    _apply_spill,
    _apply_bravery,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, drink: Drink, mammal: Beast, name: str, age: str, companion: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=mammal.type,
        label=name,
        traits=[age, "small", "curious", "brave"],
        meters={"thirst": 1.0, "carrying": 0.0, "storm": 0.0, "tiredness": 0.0},
        memes={"wonder": 1.0, "worry": 0.0, "bravery": 0.0, "trust": 0.0, "hope": 0.0},
    ))
    guide = world.add(Entity(
        id="Elder",
        kind="character",
        type="elder",
        label="the elder",
        traits=[companion, "wise"],
        meters={"thirst": 0.0},
        memes={"trust": 1.0},
    ))
    cup = world.add(Entity(
        id="Drink",
        type="cup",
        label=drink.label,
        phrase=drink.phrase,
        owner=hero.id,
        carried_by=hero.id,
        meters={"spill": 0.0},
    ))
    world.facts.update(hero=hero, guide=guide, drink_ent=cup, drink_cfg=drink, mammal=mammal)
    world.facts["cup_closed"] = True
    world.facts["omen_seen"] = False

    world.say(f"{hero.id} was a {age} {mammal.label} who loved the road before sunrise.")
    world.say(f"One day, {guide.label} gave {hero.pronoun('object')} {drink.phrase}, a {drink.taste} drink fit for a tale.")
    world.say(f'{guide.label.capitalize()} said, "Take it to the hill shrine before the moon grows pale."')

    world.para()
    world.say(f"{hero.id} set out from {setting.place}, and the air smelled of {setting.omen}.")
    propagate(world)
    world.say(f"{hero.id} wanted to bring the drink safely through the dark, because promises matter in old stories.")
    world.say(f"Along the path, a wild shadow rose and the road began to toss like a net in a storm.")
    hero.meters["storm"] += 1
    hero.memes["worry"] += 1
    propagate(world)

    world.para()
    if drink.omen_needed:
        world.say(f"{hero.id} remembered the omen and tightened the lid with both paws.")
    if hero.memes.get("bravery", 0) >= THRESHOLD:
        world.say(f"With a brave breath, {hero.id} kept going, and the cup stayed steady against the wind.")
    else:
        world.say(f"{hero.id} nearly turned back, but the thought of the elder waiting gave strength.")
    hero.meters["thirst"] = max(0.0, hero.meters["thirst"] - 1.0)
    guide.meters["thirst"] = max(0.0, guide.meters["thirst"] - 1.0)
    world.say(f"At the shrine, {hero.id} lifted the drink and shared it, and the elder smiled like sunrise.")

    hero.memes["hope"] += 1
    guide.memes["hope"] += 1
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "mountain_path": Setting(place="the mountain path", affords={"journey"}, omen="pine resin and cold stone"),
    "moon_grove": Setting(place="the moon grove", affords={"journey"}, omen="dew and silver leaves"),
    "river_road": Setting(place="the river road", affords={"journey"}, omen="reeds and wet clay"),
}

DRINKS = {
    "honey_water": Drink(
        id="honey_water",
        label="honey water",
        phrase="a terrific cup of honey water",
        taste="sweet",
        warmth="warm",
        restores="strength",
        worthy_of={"mammal"},
        omen_needed=True,
    ),
    "herb_tea": Drink(
        id="herb_tea",
        label="herb tea",
        phrase="a terrific mug of herb tea",
        taste="bright and grassy",
        warmth="warm",
        restores="calm",
        worthy_of={"mammal"},
        omen_needed=True,
    ),
    "milk_broth": Drink(
        id="milk_broth",
        label="milk broth",
        phrase="a terrific bowl of milk broth",
        taste="gentle",
        warmth="warm",
        restores="rest",
        worthy_of={"mammal"},
        omen_needed=True,
    ),
}

MAMMALS = {
    "hare": Beast(id="hare", type="hare", label="hare", phrase="a quick hare", gender="neutral", traits=["swift"]),
    "fox": Beast(id="fox", type="fox", label="fox", phrase="a sly fox", gender="neutral", traits=["clever"]),
    "badger": Beast(id="badger", type="badger", label="badger", phrase="a steady badger", gender="neutral", traits=["steadfast"]),
    "mouse": Beast(id="mouse", type="mouse", label="mouse", phrase="a small mouse", gender="neutral", traits=["small"]),
}

NAMES = ["Pip", "Sera", "Tavi", "Nia", "Orin", "Milo", "Luma", "Bren"]
AGES = ["young", "little", "small", "new"]
COMPANIONS = ["kind", "wise", "patient", "ancient"]


@dataclass
class StoryState:
    hero: Entity
    guide: Entity
    drink: Entity
    setting: Setting
    drink_cfg: Drink
    mammal: Beast
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, d, m) for s in SETTINGS for d in DRINKS for m in MAMMALS]


def explain_rejection() -> str:
    return "(No story: the requested combination does not form a reasonable mythic journey.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "drink", None):
        combos = [c for c in combos if c[1] == getattr(args, "drink", None)]
    if getattr(args, "mammal", None):
        combos = [c for c in combos if c[2] == getattr(args, "mammal", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, drink, mammal = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        drink=drink,
        mammal=mammal,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        age=getattr(args, "age", None) or rng.choice(AGES),
        companion=getattr(args, "companion", None) or rng.choice(COMPANIONS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(DRINKS, params.drink), _safe_lookup(MAMMALS, params.mammal), params.name, params.age, params.companion)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about a {f["mammal"].label}, a terrific drink, and a sign that comes before bravery.',
        f"Tell a gentle legend where {f['hero'].id} carries {f['drink_cfg'].phrase} to an elder and learns courage on the road.",
        f'Write a story with the words "terrific", "drink", and "{f["mammal"].label}" that ends with a brave choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide: Entity = _safe_fact(world, f, "guide")
    drink: Drink = _safe_fact(world, f, "drink_cfg")
    mammal: Beast = _safe_fact(world, f, "mammal")
    qa = [
        QAItem(
            question=f"Who carried the terrific drink in the story?",
            answer=f"{hero.id} carried {drink.phrase} through the dark road.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried before reaching the shrine?",
            answer=f"{hero.id} saw a foreshadowing sign, and then the storm on the road made the task feel hard.",
        ),
        QAItem(
            question=f"What did the elder want {hero.id} to deliver?",
            answer=f"The elder wanted {hero.id} to deliver {drink.phrase}.",
        ),
        QAItem(
            question=f"What kind of mammal was {hero.id}?",
            answer=f"{hero.id} was a {mammal.label}, a small mammal from the old road tale.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did bravery show up at the end?",
            answer=f"{hero.id} kept going through the storm, and that steady choice showed bravery.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mammal?",
            answer="A mammal is an animal with fur or hair that feeds its babies milk.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is a hint that something important or difficult may happen later.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing what is needed even when you feel scared.",
        ),
        QAItem(
            question="Why do people and animals drink water or broth?",
            answer="They drink to calm thirst and help their bodies feel strong again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A drink is meaningful in the story when a mammal carries it.
carrying(H,D) :- hero(H), drink(D), holds(H,D).

% An omen raises worry before the storm.
foreshadowing(H) :- hero(H), omen_seen, worry(H,W), W >= 1.

% Bravery appears when a worried hero continues with help.
brave(H) :- hero(H), worry(H,W), W >= 1, guide(G), trust(H,T), T >= 1, not turn_back(H).

valid_story(S,D,M) :- setting(S), drink(D), mammal(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DRINKS:
        lines.append(asp.fact("drink", did))
    for mid in MAMMALS:
        lines.append(asp.fact("mammal", mid))
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
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about a mammal, a terrific drink, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--mammal", choices=MAMMALS)
    ap.add_argument("--name")
    ap.add_argument("--age", choices=AGES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for s in SETTINGS:
            for d in DRINKS:
                for m in MAMMALS:
                    params = StoryParams(setting=s, drink=d, mammal=m, name="Pip", age="young", companion="wise")
                    samples.append(generate(params))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
