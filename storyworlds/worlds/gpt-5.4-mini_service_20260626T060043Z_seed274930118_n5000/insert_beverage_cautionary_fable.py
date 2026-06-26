#!/usr/bin/env python3
"""
storyworlds/worlds/insert_beverage_cautionary_fable.py
======================================================

A small cautionary fable world about a curious character, a beverage, and the
trouble that comes from trying to insert the wrong thing into it.

The seed image:
---
A little fox wanted to stir a beverage with a shiny stick and then insert a
berry into the cup "to make it nicer." The old owl warned that the cup was not a
toy. The fox ignored the warning, made a mess, and learned to pour the beverage
into a safe bowl instead.

This storyworld turns that seed into a compact simulation:
- a character desires a beverage
- a forbidden insert-choice may spoil the drink
- a warning can be heeded or ignored
- a safe substitute ends the tale with a cautionary lesson

The prose aims for a fable-like style: simple animals, clear consequence, and a
closing moral image.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    container: Optional[str] = None
    safe: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bev: object | None = None
    choice: object | None = None
    cont: object | None = None
    hero: object | None = None
    owl: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "fox": {"subject": "it", "object": "it", "possessive": "its"},
            "owl": {"subject": "it", "object": "it", "possessive": "its"},
            "rabbit": {"subject": "it", "object": "it", "possessive": "its"},
            "turtle": {"subject": "it", "object": "it", "possessive": "its"},
            "squirrel": {"subject": "it", "object": "it", "possessive": "its"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]
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
class Beverage:
    id: str
    label: str
    phrase: str
    kind: str
    hot: bool = False
    sweet: bool = False
    sour: bool = False
    clear: bool = False
    fragile: bool = True
    forms: set[str] = field(default_factory=set)
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
class InsertChoice:
    id: str
    label: str
    phrase: str
    mess: str
    effect: str
    fits: set[str] = field(default_factory=set)
    safe_in: set[str] = field(default_factory=set)
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
class Container:
    id: str
    label: str
    phrase: str
    holds: set[str]
    safe_for: set[str]
    open_top: bool = True
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
class Setting:
    place: str = "the meadow"
    tone: str = "quiet"
    kind: str = "outdoors"
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.trace_bits = list(self.trace_bits)
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    beverage: str
    insert_choice: str
    container: str
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


SETTINGS = {
    "meadow": Setting(place="the meadow", tone="gentle", kind="outdoors"),
    "orchard": Setting(place="the orchard", tone="warm", kind="outdoors"),
    "kitchen": Setting(place="the little kitchen", tone="still", kind="indoors"),
    "garden": Setting(place="the garden", tone="bright", kind="outdoors"),
}

HEROES = {
    "fox": ("fox", "clever fox"),
    "rabbit": ("rabbit", "quick rabbit"),
    "turtle": ("turtle", "patient turtle"),
    "squirrel": ("squirrel", "busy squirrel"),
}

BEVERAGES = {
    "tea": Beverage(
        id="tea",
        label="tea",
        phrase="a cup of tea",
        kind="tea",
        hot=True,
        sweet=False,
        sour=False,
        clear=True,
        forms={"cup", "mug"},
    ),
    "juice": Beverage(
        id="juice",
        label="juice",
        phrase="a glass of juice",
        kind="juice",
        hot=False,
        sweet=True,
        clear=False,
        forms={"glass", "cup"},
    ),
    "broth": Beverage(
        id="broth",
        label="broth",
        phrase="a bowl of broth",
        kind="broth",
        hot=True,
        sweet=False,
        sour=False,
        clear=False,
        forms={"bowl"},
    ),
    "lemonade": Beverage(
        id="lemonade",
        label="lemonade",
        phrase="a cup of lemonade",
        kind="lemonade",
        hot=False,
        sweet=True,
        sour=True,
        clear=False,
        forms={"cup", "jug"},
    ),
}

INSERT_CHOICES = {
    "berry": InsertChoice(
        id="berry",
        label="berry",
        phrase="a berry",
        mess="squashed fruit",
        effect="stained",
        fits={"juice", "lemonade"},
        safe_in=set(),
    ),
    "stone": InsertChoice(
        id="stone",
        label="stone",
        phrase="a smooth stone",
        mess="cloudy water",
        effect="clouded",
        fits=set(),
        safe_in=set(),
    ),
    "leaf": InsertChoice(
        id="leaf",
        label="leaf",
        phrase="a leaf",
        mess="bits of leaf",
        effect="spoiled",
        fits={"tea"},
        safe_in={"tea"},
    ),
    "spoon": InsertChoice(
        id="spoon",
        label="spoon",
        phrase="a spoon",
        mess="a clinking disturbance",
        effect="stirred",
        fits={"tea", "broth"},
        safe_in={"tea", "broth", "juice", "lemonade"},
    ),
}

CONTAINERS = {
    "cup": Container(id="cup", label="cup", phrase="a small cup", holds={"tea", "juice", "lemonade"}, safe_for={"spoon", "leaf"}),
    "mug": Container(id="mug", label="mug", phrase="a sturdy mug", holds={"tea"}, safe_for={"spoon", "leaf"}),
    "bowl": Container(id="bowl", label="bowl", phrase="a wide bowl", holds={"broth"}, safe_for={"spoon"}),
    "glass": Container(id="glass", label="glass", phrase="a clear glass", holds={"juice", "lemonade"}, safe_for={"spoon"}),
}

TRAITS = ["curious", "proud", "hasty", "thoughtful", "cheerful"]


def can_insert(bev: Beverage, choice: InsertChoice, container: Container) -> bool:
    return bev.kind in choice.fits and bev.kind in container.holds and choice.id in container.safe_for


def is_risky(bev: Beverage, choice: InsertChoice, container: Container) -> bool:
    return bev.kind in container.holds and bev.kind in choice.fits and choice.id not in container.safe_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for hero_id in HEROES:
            for bev_id, bev in BEVERAGES.items():
                for choice_id, choice in INSERT_CHOICES.items():
                    for cont_id, cont in CONTAINERS.items():
                        if bev.kind in cont.holds and (can_insert(bev, choice, cont) or is_risky(bev, choice, cont)):
                            combos.append((setting_id, hero_id, bev_id, choice_id, cont_id))
    return combos


def explain_rejection(bev: Beverage, choice: InsertChoice, cont: Container) -> str:
    return (
        f"(No story: inserting {choice.label} into {bev.label} in {cont.label} would not make a good fable. "
        f"The combination is not a plausible cautionary case.)"
    )


def _spill(world: World, actor: Entity, bev: Entity, choice: Entity) -> None:
    sig = ("spill", bev.id, choice.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    bev.meters["mess"] = bev.meters.get("mess", 0) + 1
    bev.meters["ruined"] = bev.meters.get("ruined", 0) + 1
    actor.memes["shame"] = actor.memes.get("shame", 0) + 1
    world.say(f"{actor.id} made the drink look {choice.meters.get('effect', 0) and 'wrong'}.")


def _realize(world: World, actor: Entity) -> None:
    sig = ("realize", actor.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    actor.memes["worry"] = actor.memes.get("worry", 0) + 1
    world.say(f"That was when {actor.id} felt the trouble in {its(actor)} chest.")


def its(ent: Entity) -> str:
    return "its"


def predict_result(world: World, hero: Entity, bev: Beverage, choice: InsertChoice, cont: Container) -> dict:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    bev2 = sim.get(bev.id)
    if can_insert(bev, choice, cont):
        return {"ruined": False, "lesson": True}
    if is_risky(bev, choice, cont):
        bev2.meters["mess"] = bev2.meters.get("mess", 0) + 1
        bev2.meters["ruined"] = bev2.meters.get("ruined", 0) + 1
    return {"ruined": bev2.meters.get("ruined", 0) >= THRESHOLD, "lesson": True}


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"Once in {world.setting.place}, there lived a little {trait} {hero.type}.")
    world.say(f"{hero.id} liked to learn by looking closely at every small thing.")


def desire_beverage(world: World, hero: Entity, bev: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} found {bev.phrase} and wished to enjoy {bev.pronoun('possessive')} taste.")


def warn(world: World, owl: Entity, hero: Entity, bev: Entity, choice: Entity) -> bool:
    pred = predict_result(world, hero, world.get(bev.id), _safe_lookup(INSERT_CHOICES, choice.id), CONTAINERS[world.facts["container"].id])
    if not pred["ruined"]:
        return False
    world.say(f'"Do not insert {choice.label} into the drink," said the old owl. "A cup is not a toy."')
    owl.memes["concern"] = owl.memes.get("concern", 0) + 1
    return True


def ignore(world: World, hero: Entity, choice: Entity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    world.say(f"But {hero.id} did not listen, for its curiosity was bigger than its caution.")
    world.say(f"{hero.id} reached out and tried to insert {choice.phrase} into the drink.")


def trouble(world: World, hero: Entity, bev: Entity, choice: Entity) -> None:
    bev.meters["mess"] = bev.meters.get("mess", 0) + 1
    bev.meters["ruined"] = bev.meters.get("ruined", 0) + 1
    hero.memes["regret"] = hero.memes.get("regret", 0) + 1
    world.say(f"The drink turned {choice.effect}, and the nice taste was gone.")
    world.say(f"{hero.id} blinked at the mess and knew the warning had been true.")


def safe_fix(world: World, hero: Entity, bev: Entity, cont: Entity) -> None:
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0) + 1
    world.say(f"Then {hero.id} poured the beverage into {cont.phrase} and left it plain.")
    world.say(f"That way, the {bev.label} was still useful, and nothing else needed to be inserted into it.")


def moral(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} learned that a drink is for sipping, not for stuffing with clever surprises.")
    world.say("And so the little fable ended: a cautious heart kept the table tidy.")


def tell(setting: Setting, hero_id: str, bev_id: str, choice_id: str, cont_id: str) -> World:
    world = World(setting)
    hero_type, hero_label = _safe_lookup(HEROES, hero_id)
    hero = world.add(Entity(id=hero_id, kind="character", type=hero_type, label=hero_label, traits=["little", random.choice(TRAITS)]))
    owl = world.add(Entity(id="owl", kind="character", type="owl", label="old owl", traits=["old", "wise"]))
    bev_cfg = _safe_lookup(BEVERAGES, bev_id)
    bev = world.add(Entity(id=bev_id, type=bev_cfg.kind, label=bev_cfg.label, phrase=bev_cfg.phrase))
    choice_cfg = _safe_lookup(INSERT_CHOICES, choice_id)
    choice = world.add(Entity(id=choice_id, type="thing", label=choice_cfg.label, phrase=choice_cfg.phrase))
    cont_cfg = _safe_lookup(CONTAINERS, cont_id)
    cont = world.add(Entity(id=cont_id, type="container", label=cont_cfg.label, phrase=cont_cfg.phrase))
    world.facts = {"hero": hero, "owl": owl, "beverage": bev, "choice": choice, "container": cont}

    introduce(world, hero)
    desire_beverage(world, hero, bev)
    world.para()
    world.say(f"The drink sat in {cont.phrase} beneath the quiet sky.")
    warn(world, owl, hero, bev, choice)
    ignore(world, hero, choice)
    trouble(world, hero, bev, choice)
    world.para()
    safe_fix(world, hero, bev, cont)
    moral(world, hero)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    bev = _safe_fact(world, f, "beverage")
    choice = _safe_fact(world, f, "choice")
    return [
        f'Write a short fable for a young child that includes the words "insert" and "beverage".',
        f"Tell a cautionary story about {hero.id} and {bev.label}, where someone tries to insert {choice.label} into the drink and learns a lesson.",
        f"Write a simple animal fable with a warning, a mistake, and a safe ending involving a beverage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    bev = _safe_fact(world, f, "beverage")
    choice = _safe_fact(world, f, "choice")
    cont = _safe_fact(world, f, "container")
    owl = _safe_fact(world, f, "owl")
    return [
        QAItem(
            question=f"What did {hero.id} try to insert into the {bev.label}?",
            answer=f"{hero.id} tried to insert {choice.phrase} into the {bev.label}.",
        ),
        QAItem(
            question=f"Who warned {hero.id} that the drink was not a toy?",
            answer=f"The old owl warned {hero.id} to be careful with the {bev.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} do after the {bev.label} got messy?",
            answer=f"{hero.id} poured the beverage into {cont.phrase} and left it alone so nothing else would be inserted into it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beverage?",
            answer="A beverage is a drink that people or animals sip, such as tea, juice, broth, or lemonade.",
        ),
        QAItem(
            question="Why is it risky to insert the wrong thing into a drink?",
            answer="Because the drink can become messy, unsafe, or unpleasant to taste.",
        ),
        QAItem(
            question="What is a cautionary fable?",
            answer="A cautionary fable is a short story that teaches a lesson by showing what happens when someone ignores a warning.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
beverage(B) :- bev(B).
container(C) :- cont(C).
choice(I) :- ins(I).

risky(B,I,C) :- beverage(B), choice(I), container(C), holds(C,BK), kind(B,BK), fits(I,BK), not safe_in(I,C).
safe(B,I,C) :- beverage(B), choice(I), container(C), holds(C,BK), kind(B,BK), fits(I,BK), safe_in(I,C).

valid_story(S,H,B,I,C) :- setting(S), hero(H), risky(B,I,C), beverage(B), choice(I), container(C).
good_story(S,H,B,I,C) :- setting(S), hero(H), safe(B,I,C), beverage(B), choice(I), container(C).
#show valid_story/5.
#show good_story/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, (htype, _) in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("hero_type", hid, htype))
    for bid, bev in BEVERAGES.items():
        lines.append(asp.fact("bev", bid))
        lines.append(asp.fact("kind", bid, bev.kind))
    for iid, ins in INSERT_CHOICES.items():
        lines.append(asp.fact("ins", iid))
        for k in sorted(ins.fits):
            lines.append(asp.fact("fits", iid, k))
        for k in sorted(ins.safe_in):
            lines.append(asp.fact("safe_in", iid, k))
    for cid, cont in CONTAINERS.items():
        lines.append(asp.fact("cont", cid))
        for k in sorted(cont.holds):
            lines.append(asp.fact("holds", cid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5.\n#show good_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")) | set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    import asp
    # Python gate: valid stories are the risky-but-coherent cautionary ones and safe ones.
    py = set()
    for sid in SETTINGS:
        for hid in HEROES:
            for bid, bev in BEVERAGES.items():
                for iid, ins in INSERT_CHOICES.items():
                    for cid, cont in CONTAINERS.items():
                        if bev.kind in cont.holds and ((can_insert(bev, ins, cont)) or is_risky(bev, ins, cont)):
                            py.add((sid, hid, bid, iid, cid))
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP parity matches Python gate ({len(py)} story tuples).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary fable world about inserting things into beverages.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--beverage", choices=BEVERAGES)
    ap.add_argument("--insert", dest="insert_choice", choices=INSERT_CHOICES)
    ap.add_argument("--container", choices=CONTAINERS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    bev = getattr(args, "beverage", None) or rng.choice(list(BEVERAGES))
    insert_choice = getattr(args, "insert_choice", None) or rng.choice(list(INSERT_CHOICES))
    container = getattr(args, "container", None) or rng.choice(list(CONTAINERS))
    b = _safe_lookup(BEVERAGES, bev)
    i = _safe_lookup(INSERT_CHOICES, insert_choice)
    c = _safe_lookup(CONTAINERS, container)
    if bev not in c.holds:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not (can_insert(b, i, c) or is_risky(b, i, c)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, hero=hero, beverage=bev, insert_choice=insert_choice, container=container)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params.hero, params.beverage, params.insert_choice, params.container)
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


CURATED = [
    StoryParams(setting="orchard", hero="fox", beverage="juice", insert_choice="berry", container="glass"),
    StoryParams(setting="meadow", hero="rabbit", beverage="tea", insert_choice="leaf", container="mug"),
    StoryParams(setting="garden", hero="squirrel", beverage="lemonade", insert_choice="stone", container="cup"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/5.\n#show good_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story tuples:\n")
        for t in stories:
            print("  ", t)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.beverage} / insert {p.insert_choice} / {p.container}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
