#!/usr/bin/env python3
"""
pastel_suffice_transformation_adventure.py
==========================================

A small standalone storyworld about a child, a curious transformation, and a
gentle adventure that ends in a brighter, changed place.

Seed tale:
---
A child found a plain wooden toy in a dusty attic. It looked too dull for an
adventure, so the child carried it to a workbench and painted it with pastel
colors. The toy transformed into a tiny ship, and that was enough to begin a
safe little journey.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    transformed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    mood: str
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
class ObjectType:
    id: str
    label: str
    phrase: str
    location: str
    color: str
    transformed_into: str
    use_word: str
    risk_word: str
    risk_location: str
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


@dataclass
class Charm:
    id: str
    label: str
    effect: str
    cover: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trail: list[str] = []

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
            self.trail.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.trail = list(self.trail)
        return clone


def _transformable(world: World, object_id: str) -> bool:
    obj = world.get(object_id)
    return not obj.transformed and obj.meters.get("dull", 0.0) >= THRESHOLD


def _do_transform(world: World, actor: Entity, obj: Entity, charm: Charm, narrate: bool = True) -> bool:
    if obj.transformed:
        return False
    if obj.meters.get("dull", 0.0) < THRESHOLD:
        return False
    if charm.cover != obj.location:
        return False
    sig = ("transform", obj.id, charm.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    obj.transformed = True
    obj.type = obj.transformed_into
    obj.label = obj.transformed_into
    obj.phrase = f"a small {obj.transformed_into}"
    obj.meters["dull"] = 0.0
    obj.meters["bright"] = 1.0
    actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    if narrate:
        world.say(
            f"The pastel glow touched the plain {obj.label} and it changed into a {obj.transformed_into}."
        )
    return True


def reasonableness_gate(setting: Setting, obj: ObjectType, charm: Charm) -> bool:
    return obj.location == charm.cover and obj.risk_location in setting.afford


def predict(world: World, hero: Entity, obj_id: str, charm: Charm) -> dict:
    sim = world.copy()
    _do_transform(sim, sim.get(hero.id), sim.get(obj_id), charm, narrate=False)
    obj = sim.get(obj_id)
    return {"transformed": obj.transformed}


def introduce(world: World, hero: Entity, obj: Entity) -> None:
    world.say(
        f"{hero.id} was a little curious {hero.type} who loved looking for forgotten things."
    )
    world.say(
        f"In the attic, {hero.pronoun('subject')} found {obj.phrase}, which felt too plain for an adventure."
    )


def decide(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to make {obj.it()} useful, but {hero.pronoun('possessive')} hands needed a careful plan."
    )


def warn(world: World, hero: Entity, obj: Entity, charm: Charm) -> None:
    world.say(
        f'{hero.id} whispered, "Maybe pastel colors will suffice if the workbench is the right place."'
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {charm.label} waited in the light, ready to help."
    )


def adventure_move(world: World, hero: Entity, obj: Entity) -> None:
    world.say(
        f"{hero.id} carried {obj.it()} to the workbench and set out the paints like supplies for a tiny quest."
    )


def transform_scene(world: World, hero: Entity, obj: Entity, charm: Charm) -> None:
    if predict(world, hero, obj.id, charm)["transformed"]:
        _do_transform(world, hero, obj, charm, narrate=True)


def resolution(world: World, hero: Entity, obj: Entity) -> None:
    if obj.transformed:
        world.say(
            f"That was enough: the new {obj.label} could sail on as a toy ship, and the dull attic corner felt alive."
        )
        world.say(
            f"{hero.id} smiled at the finished change, because the adventure had turned a plain thing into something splendid."
        )


def tell(setting: Setting, obj_cfg: ObjectType, charm: Charm, hero_name: str, hero_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    obj = world.add(
        Entity(
            id="object",
            type=obj_cfg.label,
            label=obj_cfg.label,
            phrase=obj_cfg.phrase,
            owner=hero.id,
            transformed=False,
            meters={"dull": 1.0},
            memes={},
        )
    )

    world.facts.update(hero=hero, obj=obj, obj_cfg=obj_cfg, charm=charm, setting=setting)

    introduce(world, hero, obj)
    world.para()
    decide(world, hero, obj)
    warn(world, hero, obj, charm)
    adventure_move(world, hero, obj)
    transform_scene(world, hero, obj, charm)
    world.para()
    resolution(world, hero, obj)
    world.facts["resolved"] = obj.transformed
    return world


SETTINGS = {
    "attic": Setting(place="the attic", mood="dusty", afford={"paint", "light"}),
    "workbench": Setting(place="the workbench room", mood="bright", afford={"paint", "light"}),
    "garden": Setting(place="the garden shed", mood="quiet", afford={"paint", "light"}),
}

OBJECTS = {
    "toy": ObjectType(
        id="toy",
        label="toy",
        phrase="a plain wooden toy",
        location="workbench",
        color="brown",
        transformed_into="tiny ship",
        use_word="useful",
        risk_word="dull",
        risk_location="workbench",
        tags={"toy", "wood", "ship"},
    ),
    "kite": ObjectType(
        id="kite",
        label="kite",
        phrase="a pale paper kite",
        location="workbench",
        color="white",
        transformed_into="bright glider",
        use_word="ready to fly",
        risk_word="plain",
        risk_location="workbench",
        tags={"kite", "paper", "wind"},
    ),
    "mask": ObjectType(
        id="mask",
        label="mask",
        phrase="a blank cardboard mask",
        location="workbench",
        color="gray",
        transformed_into="festival mask",
        use_word="ready for a show",
        risk_word="blank",
        risk_location="workbench",
        tags={"mask", "cardboard", "festival"},
    ),
}

CHARMS = {
    "pastel_box": Charm(
        id="pastel_box",
        label="pastel box",
        effect="soft color",
        cover="workbench",
    ),
    "pastel_chalk": Charm(
        id="pastel_chalk",
        label="pastel chalk",
        effect="soft color",
        cover="workbench",
    ),
    "pastel_lantern": Charm(
        id="pastel_lantern",
        label="pastel lantern",
        effect="soft light",
        cover="workbench",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "Ava", "Rosa"]
BOY_NAMES = ["Theo", "Milo", "Ben", "Eli", "Noah", "Finn"]
TRAITS = ["curious", "brave", "gentle", "lively", "careful"]


@dataclass
class StoryParams:
    setting: str
    object: str
    charm: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for o_id, obj in OBJECTS.items():
            for c_id, charm in CHARMS.items():
                if reasonableness_gate(setting, obj, charm):
                    out.append((s_id, o_id, c_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pastel transformation adventure storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "object", None) is None or c[1] == getattr(args, "object", None))
              and (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_id, object_id, charm_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, object=object_id, charm=charm_id, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle adventure story for a small child that includes the word "pastel".',
        f"Tell a story where {f['hero'].id} finds {f['obj_cfg'].phrase} and uses {f['charm'].label} to transform it.",
        f'Write a simple story where "suffice" appears naturally when a small change is enough.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    obj: Entity = _safe_fact(world, f, "obj")
    cfg: ObjectType = _safe_fact(world, f, "obj_cfg")
    charm: Charm = _safe_fact(world, f, "charm")
    qs = [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {cfg.phrase}. It looked plain at first, but it became part of the adventure.",
        ),
        QAItem(
            question=f"What did {hero.id} use to change the plain {cfg.label}?",
            answer=f"{hero.id} used {charm.label}, which gave the object a soft pastel change.",
        ),
        QAItem(
            question=f"What did the {cfg.label} turn into?",
            answer=f"It turned into a {cfg.transformed_into}. That new shape was enough to make the adventure work.",
        ),
    ]
    if f.get("resolved"):
        qs.append(
            QAItem(
                question=f"Why did {hero.id} say pastel colors would suffice?",
                answer=f"{hero.id} said that because the object only needed a careful change, not a big repair. The pastel colors were enough to bring it to life.",
            )
        )
    return qs


WORLD_KNOWLEDGE = {
    "pastel": [
        QAItem(
            question="What are pastel colors?",
            answer="Pastel colors are soft, light colors like pale pink, blue, green, or yellow.",
        )
    ],
    "suffice": [
        QAItem(
            question="What does suffice mean?",
            answer="If something suffices, it is enough for the job or the moment.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change that makes something become different from before.",
        )
    ],
    "adventure": [
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting journey or experience where something interesting happens.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [WORLD_KNOWLEDGE["pastel"][0], WORLD_KNOWLEDGE["suffice"][0], WORLD_KNOWLEDGE["transformation"][0], WORLD_KNOWLEDGE["adventure"][0]]


ASP_RULES = r"""
valid_combo(S,O,C) :- setting(S), object(O), charm(C),
    setting_afford(S, workbench),
    object_at(O, workbench),
    charm_cover(C, workbench).

shows_transformation(O) :- valid_combo(_,O,_), object_dull(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s_id in SETTINGS:
        lines.append(asp.fact("setting", s_id))
        lines.append(asp.fact("setting_afford", s_id, "workbench"))
    for o_id, obj in OBJECTS.items():
        lines.append(asp.fact("object", o_id))
        lines.append(asp.fact("object_at", o_id, obj.location))
        lines.append(asp.fact("object_dull", o_id))
    for c_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", c_id))
        lines.append(asp.fact("charm_cover", c_id, charm.cover))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    obj_cfg = _safe_lookup(OBJECTS, params.object)
    charm = _safe_lookup(CHARMS, params.charm)
    world = tell(setting, obj_cfg, charm, params.name, params.gender)
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
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.transformed:
                bits.append("transformed=True")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== (3) World knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(setting=s, object=o, charm=c, name="Ari", gender="girl", trait="curious"))
                   for s, o, c in valid_combos()]
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
