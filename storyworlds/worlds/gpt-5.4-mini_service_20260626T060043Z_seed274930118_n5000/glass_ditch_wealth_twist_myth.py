#!/usr/bin/env python3
"""
storyworlds/worlds/glass_ditch_wealth_twist_myth.py
====================================================

A compact myth-style storyworld about glass, a ditch, and wealth, with a
careful twist: what looks broken, poor, or lost can become a source of treasure
when the characters learn how to handle it.

Seed tale shape:
- A young hero finds a shard or vessel of glass near a ditch.
- A guardian fears the glass will break and the wealth will be lost.
- A safer, wiser choice reveals the true value of the thing.

The world is state-driven: physical meters track fragility, wetness, hiddenness,
and wealth; emotional memes track hope, fear, greed, trust, and wonder.
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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ditch: object | None = None
    guardian: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "maiden"}
        male = {"boy", "father", "man", "king", "priest"}
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
    feature: str
    weather: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    value: str
    fragile: bool = True
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


@dataclass
class Twist:
    id: str
    reveal: str
    method: str
    ending: str
    truth: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "moon_ditch": Setting(
        place="the moonlit ditch",
        feature="a silver-bright ditch",
        weather="night",
        affords={"find", "lift", "cross"},
    ),
    "orchard_ditch": Setting(
        place="the orchard ditch",
        feature="a ditch under old apple trees",
        weather="breezy",
        affords={"find", "lift", "cross"},
    ),
    "temple_ditch": Setting(
        place="the temple ditch",
        feature="a ditch beside the temple wall",
        weather="warm",
        affords={"find", "lift", "cross"},
    ),
}

TREASURES = {
    "glass_cup": Treasure(
        id="glass_cup",
        label="glass cup",
        phrase="a clear glass cup",
        type="cup",
        region="hands",
        value="wealth",
    ),
    "glass_jar": Treasure(
        id="glass_jar",
        label="glass jar",
        phrase="a green glass jar",
        type="jar",
        region="hands",
        value="wealth",
    ),
    "glass_beads": Treasure(
        id="glass_beads",
        label="glass beads",
        phrase="a string of glass beads",
        type="beads",
        region="hands",
        value="wealth",
        plural=True,
    ),
}

TWISTS = {
    "hidden_map": Twist(
        id="hidden_map",
        reveal="The glass was not ordinary at all; it held a faint map inside it.",
        method="held it to the moonlight",
        ending="the moonlight drew a bright path across the ditch",
        truth="The real wealth was the hidden route to the old buried chest.",
    ),
    "water_song": Twist(
        id="water_song",
        reveal="The glass sang softly when the wind touched it.",
        method="set it on a stone",
        ending="the ditch answered with a clear little song",
        truth="The real wealth was the song that led the village to clean water.",
    ),
    "river_lens": Twist(
        id="river_lens",
        reveal="The glass bent the world like a tiny eye.",
        method="looked through it",
        ending="the field beyond the ditch shone where the buried coins were",
        truth="The real wealth was the hidden coin-cache where the grass bent low.",
    ),
}

ROLES = {
    "girl": ["Asha", "Mina", "Suri", "Leela", "Nora"],
    "boy": ["Ilan", "Taro", "Marek", "Jori", "Pavel"],
}

GUARDIANS = ["mother", "father", "elder", "priest", "grandmother"]
TRAITS = ["curious", "brave", "gentle", "restless", "hopeful", "stubborn"]


@dataclass
class StoryParams:
    place: str
    treasure: str
    twist: str
    name: str
    gender: str
    guardian: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, w) for p in SETTINGS for t in TREASURES for w in TWISTS]


def prize_at_risk(setting: Setting, treasure: Treasure) -> bool:
    return treasure.region in {"hands", "ground", "feet"}


def select_twist(treasure: Treasure) -> Twist:
    return TWISTS["hidden_map"] if treasure.id == "glass_jar" else TWISTS["water_song"] if treasure.id == "glass_cup" else TWISTS["river_lens"]


def explain_rejection() -> str:
    return "(No story: this world needs a glass treasure, a ditch, and a twist that reveals wealth in a believable way.)"


ASP_RULES = r"""
place(P) :- setting(P).
treasure(T) :- glass(T).
twist(W) :- twist_id(W).

valid(P,T,W) :- setting(P), glass(T), twist_id(W).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("glass", tid))
        lines.append(asp.fact("treasure_region", tid, t.region))
    for wid, w in TWISTS.items():
        lines.append(asp.fact("twist_id", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world with glass, a ditch, wealth, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=GUARDIANS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "treasure", None):
        combos = [c for c in combos if c[1] == getattr(args, "treasure", None)]
    if getattr(args, "twist", None):
        combos = [c for c in combos if c[2] == getattr(args, "twist", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, treasure, twist = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(ROLES, gender))
    guardian = getattr(args, "guardian", None) or rng.choice(GUARDIANS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, treasure=treasure, twist=twist, name=name, gender=gender, guardian=guardian, trait=trait)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    treasure_cfg = _safe_lookup(TREASURES, params.treasure)
    twist_cfg = _safe_lookup(TWISTS, params.twist)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    guardian = world.add(Entity(id="Guardian", kind="character", type=params.guardian, label=f"the {params.guardian}"))
    treasure = world.add(Entity(id="Treasure", type=treasure_cfg.type, label=treasure_cfg.label, phrase=treasure_cfg.phrase, region=treasure_cfg.region, plural=treasure_cfg.plural, owner=hero.id))
    ditch = world.add(Entity(id="Ditch", type="ditch", label="the ditch"))
    # state
    hero.memes["wonder"] = 1
    guardian.memes["fear"] = 1
    treasure.meters["hidden"] = 1
    treasure.meters["fragile"] = 1
    treasure.meters["wealth"] = 1

    world.say(f"Long ago, in {setting.place}, {hero.id} was a {params.trait} {params.gender} who loved old stories.")
    world.say(f"{hero.id} often wandered near {setting.feature}, where {setting.weather} air rested on the grass.")
    world.say(f"One day {hero.id} found {treasure.phrase} beside the ditch, and {hero.pronoun('possessive')} eyes grew wide at the shine.")

    world.para()
    world.say(f"{guardian.label.capitalize()} hurried over and frowned at the glass.")
    world.say(f'"Do not lift it too quickly," {guardian.pronoun()} warned. "Glass can split, and wealth can vanish if we are careless."')
    hero.memes["hope"] = 1
    hero.memes["greed"] = 1 if treasure.value == "wealth" else 0.5

    world.say(f"But {hero.id} did not want to leave it in the ditch, where mud could hide its bright edges.")
    world.say(f"{hero.id} knelt down, cupped {hero.pronoun('possessive')} hands, and lifted the glass with a slow, careful breath.")
    treasure.meters["held"] = 1
    treasure.meters["wet"] = 0.0

    world.para()
    world.say(f"Then came the twist.")
    world.say(twist_cfg.reveal)
    world.say(f"When {hero.id} {twist_cfg.method}, {twist_cfg.ending}.")
    world.say(twist_cfg.truth)

    world.say(f"{guardian.label.capitalize()} softened at once, because the feared thing had become a guide instead of a loss.")
    hero.memes["trust"] = 1
    guardian.memes["relief"] = 1
    hero.memes["greed"] = 0.0
    treasure.meters["hidden"] = 0.0
    treasure.meters["wealth"] = 2.0

    world.para()
    if twist_cfg.id == "hidden_map":
        world.say(f"Together they followed the faint path the glass had shown, and at last they found the buried chest of wealth under the roots.")
    elif twist_cfg.id == "water_song":
        world.say(f"Together they followed the song, and at last they found the spring that filled the village jars for many days.")
    else:
        world.say(f"Together they followed the bent light, and at last they found the coins that had slept beneath the grass.")
    world.say(f"{hero.id} laughed, {guardian.label} smiled, and the ditch was no longer a place of loss but a place of wonder.")
    world.facts.update(hero=hero, guardian=guardian, treasure=treasure, twist=twist_cfg, setting=setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short myth about {f['hero'].id} finding glass near a ditch and discovering wealth through a twist.",
        f"Tell a child-friendly story where a {f['guardian'].type} worries that glass will break, but the ending reveals a wiser treasure.",
        f"Write a gentle myth with the words glass, ditch, and wealth, ending with a surprising twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guardian = _safe_fact(world, f, "guardian")
    treasure = _safe_fact(world, f, "treasure")
    twist = _safe_fact(world, f, "twist")
    return [
        QAItem(
            question=f"Who found the glass treasure near the ditch?",
            answer=f"{hero.id} found {treasure.phrase} near the ditch.",
        ),
        QAItem(
            question=f"Why did the {guardian.type} worry about the glass?",
            answer=f"The {guardian.type} worried because glass can break if it is handled too fast or too roughly.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the glass was not just pretty; it revealed {twist.truth.lower()}",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the ditch felt like a place of wonder, and the hidden wealth was safely found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is glass?",
            answer="Glass is a hard, clear material that can be shaped into cups, jars, beads, and windows.",
        ),
        QAItem(
            question="What is a ditch?",
            answer="A ditch is a long, narrow hollow in the ground, often dug to guide water or mark a border.",
        ),
        QAItem(
            question="What does wealth mean?",
            answer="Wealth means having valuable things, like treasure, gold, good food, or plenty of useful resources.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes how you understand what was happening.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            for treasure in TREASURES:
                for twist in TWISTS:
                    params = StoryParams(
                        place=place,
                        treasure=treasure,
                        twist=twist,
                        name="Asha",
                        gender="girl",
                        guardian="elder",
                        trait="curious",
                    )
                    params.seed = base_seed
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
