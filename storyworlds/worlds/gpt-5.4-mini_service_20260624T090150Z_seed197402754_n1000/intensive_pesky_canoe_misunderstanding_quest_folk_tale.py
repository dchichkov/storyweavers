#!/usr/bin/env python3
"""
storyworlds/worlds/intensive_pesky_canoe_misunderstanding_quest_folk_tale.py
============================================================================

A small folk-tale storyworld about an intensive, pesky canoe misunderstanding
during a quest.

The seed tale behind this world:
---
A little child wanted to go on a quest across the river in a canoe. A pesky
misunderstanding made everyone think the canoe was too small or too fragile.
After some worry and a careful explanation, the truth came out: the canoe was
fine, and the quest could continue in a safe, gentle way.
---

The world model tracks:
- physical meters: distance, readiness, repair, calm, wear
- emotional memes: hope, worry, confusion, trust, delight

The story is generated from state, not from a frozen template swap. The tale
can vary in names, roles, setting, and the quest object, while keeping the
core misunderstanding-and-resolution arc intact.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    in_canoe: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    c: object | None = None
    elder: object | None = None
    hero: object | None = None
    q: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    terrain: str
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
class Quest:
    id: str
    goal: str
    across: str
    travel: str
    treasure: str
    token: str
    risk: str
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
class Canoe:
    id: str
    label: str
    size: str
    sturdy: bool
    can_carry: int
    fix: str
    detail: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.m("confusion") < THRESHOLD:
            continue
        sig = ("confusion", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] = hero.e("worry") + 1
        out.append(f"{hero.noun().capitalize()} felt more and more unsure.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.m("calm") < THRESHOLD:
            continue
        sig = ("calm", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] = max(0.0, hero.e("worry") - 1)
        hero.memes["trust"] = hero.e("trust") + 1
        out.append(f"{hero.noun().capitalize()} breathed easier.")
    return out


def _r_readiness(world: World) -> list[str]:
    out: list[str] = []
    canoe = world.get("canoe")
    if canoe.m("repair") >= THRESHOLD and canoe.m("ready") < THRESHOLD:
        sig = ("ready",)
        if sig not in world.fired:
            world.fired.add(sig)
            canoe.meters["ready"] = 1.0
            out.append("The canoe was ready again.")
    return out


CAUSAL_RULES = [
    _r_confusion,
    _r_calm,
    _r_readiness,
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


def predict_quest(world: World, hero: Entity, quest: Quest) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["confusion"] += 1
    sim.get("canoe").meters["wear"] += 1
    propagate(sim, narrate=False)
    canoe = sim.get("canoe")
    return {
        "safe": canoe.m("ready") >= THRESHOLD and sim.get(hero.id).e("worry") < 2,
        "worry": sim.get(hero.id).e("worry"),
    }


def can_handle_quest(quest: Quest, canoe: Canoe) -> bool:
    return quest.goal in {"quest", "crossing"} and canoe.sturdy


def reasonableness_gate(quest: Quest, canoe: Canoe) -> bool:
    return can_handle_quest(quest, canoe) and quest.token in {"map", "lamp", "basket", "song"}


def introduce(hero: Entity) -> str:
    return f"{hero.noun().capitalize()} was a little {hero.type} who loved a brave quest."


def setting_detail(setting: Setting) -> str:
    if setting.terrain == "riverbank":
        return "The river sang softly beside the reeds, and the bank smelled like rain and mud."
    if setting.terrain == "forest":
        return "The trees stood close together, and the path curled like a ribbon."
    return f"{setting.place.capitalize()} felt old and kindly, like a place that remembered many stories."


def quest_setup(hero: Entity, quest: Quest, canoe: Canoe) -> str:
    return (
        f"{hero.noun().capitalize()} dreamed of a quest to find {quest.treasure} across {quest.across} "
        f"in the {canoe.label}. The {canoe.label} was {canoe.size} but sturdy, and {canoe.detail}."
    )


def misunderstanding_line(hero: Entity, quest: Quest, canoe: Canoe) -> str:
    return (
        f"Then a pesky misunderstanding spread like wind in tall grass: someone thought the {canoe.label} "
        f"was too frail for the quest, and {hero.pronoun('possessive')} heart sank with worry."
    )


def clarify(world: World, elder: Entity, hero: Entity, canoe: Canoe, quest: Quest) -> str:
    hero.meters["confusion"] += 1
    hero.memes["worry"] = hero.e("worry") + 1
    hero.memes["hope"] = hero.e("hope") + 1
    world.get("canoe").meters["wear"] += 1
    world.get("canoe").meters["repair"] += 1
    propagate(world, narrate=False)
    return (
        f"'{canoe.fix},' said {elder.noun()}. 'This canoe is small, yes, but it is {canoe.size} and {canoe.sturdy and 'sturdy' or 'carefully made'}."
        f" It can carry {canoe.can_carry} little travelers, and the quest only needs a calm pair of hands.'"
    )


def resolution(hero: Entity, elder: Entity, canoe: Canoe, quest: Quest) -> list[str]:
    hero.meters["calm"] += 1
    hero.memes["trust"] = hero.e("trust") + 1
    hero.memes["delight"] = hero.e("delight") + 1
    hero.memes["worry"] = max(0.0, hero.e("worry") - 1)
    return [
        f"{hero.noun().capitalize()} listened, and the worry in {hero.pronoun('possessive')} chest grew lighter.",
        f"Together they stepped into the {canoe.label}, pushed from the bank, and let the current carry them to {quest.treasure}.",
        f"In the end, the canoe rocked gently, the quest stayed safe, and the pesky misunderstanding floated away like a leaf on the water.",
    ]


SETTINGS = {
    "riverbank": Setting(place="the riverbank", terrain="riverbank", affords={"quest", "canoe"}),
    "harbor": Setting(place="the harbor", terrain="riverbank", affords={"quest", "canoe"}),
    "woodland": Setting(place="the woodland edge", terrain="forest", affords={"quest"}),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        goal="quest",
        across="the river",
        travel="by canoe",
        treasure="the lost lantern",
        token="lamp",
        risk="the lantern could be left behind in the reeds",
        tags={"quest", "misunderstanding", "canoe"},
    ),
    "berries": Quest(
        id="berries",
        goal="quest",
        across="the marsh",
        travel="by canoe",
        treasure="the red berries",
        token="basket",
        risk="the berries could be bruised by a rough ride",
        tags={"quest", "canoe"},
    ),
    "song": Quest(
        id="song",
        goal="quest",
        across="the far bank",
        travel="by canoe",
        treasure="the old song",
        token="song",
        risk="the song could be forgotten if nobody crossed",
        tags={"quest", "misunderstanding"},
    ),
}

CANOES = {
    "little_canoe": Canoe(
        id="canoe",
        label="canoe",
        size="small",
        sturdy=True,
        can_carry=2,
        fix="It only needed a gentle check and a steady hand",
        detail="its planks were tight and its paddle was smooth",
    ),
    "old_canoe": Canoe(
        id="canoe",
        label="canoe",
        size="intensive and carefully mended",
        sturdy=True,
        can_carry=3,
        fix="It had already been mended and tested twice",
        detail="its rope knots were neat and its seat was dry",
    ),
}

NAMES = {
    "girl": ["Mira", "Lena", "Tara", "Ivy", "Nina"],
    "boy": ["Perrin", "Jory", "Bram", "Tobin", "Owen"],
}
KINDS = {"girl": "girl", "boy": "boy"}
ELDERS = ["grandmother", "grandfather", "aunt", "uncle"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    canoe: str
    name: str
    gender: str
    elder: str
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


CURATED = [
    StoryParams(setting="riverbank", quest="lantern", canoe="little_canoe", name="Mira", gender="girl", elder="grandmother"),
    StoryParams(setting="harbor", quest="berries", canoe="old_canoe", name="Bram", gender="boy", elder="uncle"),
    StoryParams(setting="riverbank", quest="song", canoe="little_canoe", name="Tara", gender="girl", elder="aunt"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: an intensive, pesky canoe misunderstanding quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--canoe", choices=CANOES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
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
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    canoe = getattr(args, "canoe", None) or rng.choice(list(CANOES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    elder = getattr(args, "elder", None) or rng.choice(ELDERS)
    if not reasonableness_gate(_safe_lookup(QUESTS, quest), _safe_lookup(CANOES, canoe)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, quest=quest, canoe=canoe, name=name, gender=gender, elder=elder)


def tell(setting: Setting, quest: Quest, canoe: Canoe, hero_name: str, gender: str, elder_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=hero_name))
    elder = world.add(Entity(id="elder", kind="character", type=elder_kind, label=elder_kind))
    q = world.add(Entity(id="quest", type="quest", label=quest.id, phrase=quest.goal))
    c = world.add(Entity(id="canoe", type="canoe", label="canoe"))
    c.meters.update({"wear": 0.0, "repair": 0.0, "ready": 1.0 if canoe.sturdy else 0.0})
    c.memes.update({"trust": 0.0})

    world.say(introduce(hero))
    world.say(setting_detail(setting))
    world.say(quest_setup(hero, quest, canoe))
    world.para()
    world.say(f"But there was trouble: {quest.risk}.")
    world.say(misunderstanding_line(hero, quest, canoe))
    world.say(f"{elder.noun().capitalize()} noticed the worry and came closer to speak plainly.")
    world.para()
    world.say(clarify(world, elder, hero, canoe, quest))
    world.say(f"{hero.noun().capitalize()} looked at the canoe again and saw that {canoe.detail}.")
    world.para()
    for line in resolution(hero, elder, canoe, quest):
        world.say(line)

    world.facts.update(hero=hero, elder=elder, quest=quest, canoe=canoe, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    canoe = _safe_fact(world, f, "canoe")
    return [
        "Write a folk-tale story for a young child about an intensive, pesky canoe misunderstanding during a quest.",
        f"Tell a gentle story where {hero.label} must travel {quest.across} in a {canoe.label}, but a misunderstanding causes worry before the quest can continue.",
        f"Write a simple story that includes the words 'intensive', 'pesky', and 'canoe' and ends with a calm explanation that saves the quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    quest = _safe_fact(world, f, "quest")
    canoe = _safe_fact(world, f, "canoe")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, who went on a quest with help from {elder.label}.",
        ),
        QAItem(
            question=f"What caused the trouble in the middle of the story?",
            answer=f"A pesky misunderstanding made people worry that the canoe was too fragile for the quest.",
        ),
        QAItem(
            question=f"What did the canoe help the hero do in the end?",
            answer=f"It helped {hero.label} cross {quest.across} and continue the quest safely.",
        ),
        QAItem(
            question=f"How did the elder help?",
            answer=f"{elder.label.capitalize()} explained that the canoe was sturdy, calm, and ready for the trip.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "canoe": [
        QAItem(
            question="What is a canoe?",
            answer="A canoe is a small boat that people can paddle on rivers, lakes, or calm water.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal, like finding something lost or reaching a special place.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea and worries before the truth is clear.",
        )
    ],
    "folk": [
        QAItem(
            question="What makes a folk tale feel special?",
            answer="A folk tale often sounds old and warm, with a brave problem, a kind helper, and a clear ending.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["canoe"] + WORLD_KNOWLEDGE["quest"] + WORLD_KNOWLEDGE["misunderstanding"] + WORLD_KNOWLEDGE["folk"]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H), type(H,girl).
hero(H) :- character(H), type(H,boy).

misunderstanding(H) :- confusion(H), worry(H).
quest_ready(C) :- canoe(C), sturdy(C), ready(C).

can_continue(H,Q,C) :- hero(H), quest(Q), canoe(C), misunderstanding(H), quest_ready(C).
resolved(H) :- can_continue(H,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("terrain", sid, s.terrain))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("treasure", qid, q.treasure))
        lines.append(asp.fact("risk", qid, q.risk))
        lines.append(asp.fact("token", qid, q.token))
    for cid, c in CANOES.items():
        lines.append(asp.fact("canoe", cid))
        if c.sturdy:
            lines.append(asp.fact("sturdy", cid))
        lines.append(asp.fact("ready", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_continue/3."))
    asp_set = set(asp.atoms(model, "can_continue"))
    py_set = set()
    for sid, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for cid, canoe in CANOES.items():
                if setting.affords and reasonableness_gate(quest, canoe):
                    py_set.add((sid, qid, cid))
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(asp_set)} combinations).")
        return 0
    print("MISMATCH:")
    if asp_set - py_set:
        print(" only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print(" only in Python:", sorted(py_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(QUESTS, params.quest),
        _safe_lookup(CANOES, params.canoe),
        params.name,
        params.gender,
        params.elder,
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


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_continue/3."))
    return sorted(set(asp.atoms(model, "can_continue")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show can_continue/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} compatible quest combinations:")
        for v in vals:
            print("  ", v)
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
            header = f"### {p.name}: {p.quest} in {p.setting} with {p.canoe}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
