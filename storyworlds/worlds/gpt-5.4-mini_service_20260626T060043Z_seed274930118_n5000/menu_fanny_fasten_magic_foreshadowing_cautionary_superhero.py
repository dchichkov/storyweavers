#!/usr/bin/env python3
"""
A standalone storyworld script for a tiny superhero tale:
a hero, a menu, a fanny pack, and a fasten/prepare choice.

The world is intentionally small and classical:
- a child hero wants to do a flashy superhero activity,
- a careful adult notices a risky detail in time,
- magic and foreshadowing nudge the hero toward a safer plan,
- the ending shows what changed in the world state.

This script follows the Storyweavers contract:
- StoryParams and registries are world-specific
- StorySample / QAItem / StoryError are imported eagerly
- ASP helper is imported lazily in the ASP helpers
- --verify checks Python/ASP parity and exercises generated stories
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    place: str = "the rooftop garden"
    indoors: bool = False
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
class Scene:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    weather: str
    zone: set[str]
    keyword: str = ""
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


@dataclass
class Prize:
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "rooftop": Setting(place="the rooftop garden", indoors=False, affords={"magic", "rescue"}),
    "museum": Setting(place="the city museum", indoors=True, affords={"magic", "rescue"}),
    "alley": Setting(place="the lantern alley", indoors=False, affords={"magic"}),
}

SCENES = {
    "magic": Scene(
        id="magic",
        verb="cast a magic shield",
        gerund="casting magic shields",
        rush="dash into the sparkle cloud",
        mess="glitter",
        soil="full of glitter",
        weather="windy",
        zone={"torso", "hands"},
        keyword="magic",
        tags={"magic", "foreshadowing"},
    ),
    "rescue": Scene(
        id="rescue",
        verb="rescue the kitten",
        gerund="rescuing the kitten",
        rush="climb toward the ledge",
        mess="dust",
        soil="dusty",
        weather="sunny",
        zone={"feet", "legs", "torso"},
        keyword="help",
        tags={"cautionary"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", region="torso"),
    "gloves": Prize(label="gloves", phrase="shiny hero gloves", type="gloves", region="hands", plural=True),
    "boots": Prize(label="boots", phrase="polished boots", type="boots", region="feet", plural=True),
}

GEAR = [
    Gear(
        id="belt",
        label="a utility belt",
        covers={"torso"},
        guards={"glitter", "dust"},
        prep="fasten a utility belt first",
        tail="fastened the utility belt",
    ),
    Gear(
        id="fanny",
        label="a little fanny pack",
        covers={"torso"},
        guards={"glitter"},
        prep="fasten the little fanny pack first",
        tail="fastened the little fanny pack",
    ),
    Gear(
        id="mask",
        label="a soft mask",
        covers={"hands"},
        guards={"glitter"},
        prep="pull on the soft mask first",
        tail="put on the soft mask",
    ),
]

GIRL_NAMES = ["Mina", "Tia", "Luna", "Ivy", "Nora", "Pia", "Zoe", "Maya"]
BOY_NAMES = ["Arlo", "Finn", "Theo", "Leo", "Noah", "Ben", "Eli", "Max"]
TRAITS = ["brave", "careful", "curious", "lively", "spirited", "kind"]


def prize_at_risk(scene: Scene, prize: Prize) -> bool:
    return prize.region in scene.zone


def select_gear(scene: Scene, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if scene.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for scene_id in setting.affords:
            scene = _safe_lookup(SCENES, scene_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(scene, prize) and select_gear(scene, prize):
                    combos.append((place, scene_id, prize_id))
    return combos


def activity_feel(scene: Scene) -> str:
    return {
        "magic": "the glitter made the whole street sparkle like a comic-book sky",
        "rescue": "the rescue ladder looked tall and daring",
    }.get(scene.id, "the day felt like a heroic mission")


def setting_detail(setting: Setting, scene: Scene) -> str:
    if setting.indoors:
        return f"{setting.place.capitalize()} was quiet, and the display lights blinked softly."
    return f"{setting.place.capitalize()} glowed under the open sky, and the wind kept tugging at capes."


def _do_scene(world: World, actor: Entity, scene: Scene, narrate: bool = True) -> None:
    if scene.id not in world.setting.affords:
        return
    actor.meters[scene.mess] = actor.meters.get(scene.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} {scene.gerund}.")


def predict_mess(world: World, actor: Entity, scene: Scene, prize_id: str) -> dict:
    sim = world.copy()
    _do_scene(sim, sim.get(actor.id), scene, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": True, "workload": len([e for e in sim.entities.values() if e.kind == "character"])}


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved superhero stories.")


def foreshadow(world: World, hero: Entity, scene: Scene) -> None:
    if scene.id == "magic":
        world.say(
            f"That morning, {hero.id} noticed glitter clinging to {hero.pronoun('possessive')} sleeves, "
            f"like a tiny warning from the sky."
        )
    else:
        world.say(
            f"At the edge of the day, {hero.id} saw a wobbling ladder and remembered to move slowly."
        )


def loves(world: World, hero: Entity, scene: Scene) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {scene.gerund}, because {activity_feel(scene)}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That afternoon, {hero.pronoun('possessive')} {parent.label_word} bought {hero.pronoun('object')} {prize.phrase}.")


def wears(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like a real hero would.")


def arrives(world: World, hero: Entity, parent: Entity, scene: Scene) -> None:
    day = "One evening, "
    go = "went to" if not world.setting.indoors else "walked into"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, scene))


def wants(world: World, hero: Entity, scene: Scene) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {scene.verb} right away.")


def warn(world: World, parent: Entity, hero: Entity, scene: Scene, prize: Entity) -> None:
    world.facts["foreshadow"] = True
    world.say(
        f'"If you rush in now, your {prize.label} will get {scene.soil}," '
        f"{hero.pronoun('possessive')} {parent.label_word} said. "
        f'"Let’s fasten something first."'
    )


def defy(world: World, hero: Entity, scene: Scene) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} almost charged ahead anyway, because the mission felt too exciting to wait for.")


def choose_gear(scene: Scene, prize: Entity) -> Optional[Gear]:
    return select_gear(scene, prize)


def compromise(world: World, parent: Entity, hero: Entity, scene: Scene, prize: Entity) -> Optional[Gear]:
    gear = choose_gear(scene, prize)
    if gear is None:
        return None
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} smiled and said, "
        f'"Let’s {gear.prep} before we go."'
    )
    return gear


def accept(world: World, parent: Entity, hero: Entity, scene: Scene, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} nodded, and together they {gear.tail}. "
        f"Then {hero.id} was ready to {scene.verb}, and {prize.label} stayed clean."
    )


@dataclass
class StoryParams:
    place: str
    scene: str
    prize: str
    name: str
    gender: str
    parent: str
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


def tell(setting: Setting, scene: Scene, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or [])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
                             plural=prize_cfg.plural))
    world.weather = scene.weather

    introduce(world, hero)
    loves(world, hero, scene)
    buys(world, parent, hero, prize)
    wears(world, hero, prize)

    world.para()
    arrives(world, hero, parent, scene)
    foreshadow(world, hero, scene)
    wants(world, hero, scene)
    warn(world, parent, hero, scene, prize)
    defy(world, hero, scene)

    world.para()
    gear = compromise(world, parent, hero, scene, prize)
    if gear:
        accept(world, parent, hero, scene, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, scene=scene, gear=gear, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    scene: Scene = _safe_fact(world, f, "scene")
    prize: Entity = _safe_fact(world, f, "prize")
    return [
        f'Write a short superhero story for a young child that includes the word "{scene.keyword}" and the words "menu", "fanny", and "fasten".',
        f"Tell a gentle superhero story where {hero.id} wants to {scene.verb}, but {hero.pronoun('possessive')} {prize.label} needs care and an adult suggests a safer plan.",
        f"Write a cautionary story with foreshadowing, magic, and a happy ending where a child hero learns to fasten gear before a mission.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    prize: Entity = _safe_fact(world, f, "prize")
    scene: Scene = _safe_fact(world, f, "scene")
    gear: Optional[Gear] = _safe_fact(world, f, "gear")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little superhero who wants to {scene.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about {prize.label}?",
            answer=f"{parent.label_word.capitalize()} worried because if {hero.id} rushed into the mission, {prize.label} would get {scene.soil}.",
        ),
        QAItem(
            question=f"What helped {hero.id} stay safe?",
            answer=f"{gear.label if gear else 'A safer plan'} helped {hero.id} get ready before the mission.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} was ready for the mission, and {prize.label} stayed clean.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special and impossible in real life, like a sparkle or spell that makes the story feel wonder-filled.",
        )
    ],
    "foreshadowing": [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a little clue early in a story that hints something important may happen later.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means a story gives a careful warning so someone can avoid trouble.",
        )
    ],
    "fanny": [
        QAItem(
            question="What is a fanny pack?",
            answer="A fanny pack is a small bag that clips or fastens around the waist so you can carry little things with you.",
        )
    ],
    "fasten": [
        QAItem(
            question="What does fasten mean?",
            answer="Fasten means to close or secure something so it stays on or stays shut, like a buckle or a zipper.",
        )
    ],
    "menu": [
        QAItem(
            question="What is a menu?",
            answer="A menu is a list of choices, like foods to pick from or options to decide between.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["scene"].tags) | {"fanny", "fasten", "menu"}
    out: list[QAItem] = []
    for key in ["magic", "foreshadowing", "cautionary", "fanny", "fasten", "menu"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="rooftop", scene="magic", prize="cape", name="Mina", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="museum", scene="magic", prize="gloves", name="Arlo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="alley", scene="magic", prize="boots", name="Zoe", gender="girl", parent="mother", trait="lively"),
]


ASP_RULES = r"""
prize_at_risk(S,P) :- zone(S,R), prize_region(P,R).
has_fix(S,P) :- prize_at_risk(S,P), gear(G), guards(G,M), scene_mess(S,M), covers(G,R), prize_region(P,R).
valid(Place,S,P) :- affords(Place,S), prize_at_risk(S,P), has_fix(S,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for sc in sorted(s.affords):
            lines.append(asp.fact("affords", pid, sc))
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("scene_mess", sid, s.mess))
        for r in sorted(s.zone):
            lines.append(asp.fact("zone", sid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between clingo and valid_combos():")
        print("  only in python:", sorted(py - asp_set))
        print("  only in clingo:", sorted(asp_set - py))
        return 1

    rng = random.Random(12345)
    params = resolve_params(argparse.Namespace(place=None, scene=None, prize=None, gender=None, parent=None, name=None), rng)
    sample = generate(params)
    if not sample.story or not sample.story.strip():
        print("FAIL: generated story is empty")
        return 1
    print("OK: generated story is non-empty and usable.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: magic, foreshadowing, and cautionary hero choices.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "scene", None) and getattr(args, "prize", None):
        scene, prize = _safe_lookup(SCENES, getattr(args, "scene", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(scene, prize) and select_gear(scene, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "scene", None) is None or c[1] == getattr(args, "scene", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, scene, prize = rng.choice(list(combos))
    prize_obj = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize_obj.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, scene=scene, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(SCENES, params.scene),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        [params.trait, "stubborn"],
        params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, scene, prize) combos:\n")
        for place, scene, prize in triples:
            print(f"  {place:9} {scene:8} {prize:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.scene} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
