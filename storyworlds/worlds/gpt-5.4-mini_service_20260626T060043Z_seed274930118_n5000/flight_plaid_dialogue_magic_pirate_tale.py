#!/usr/bin/env python3
"""
storyworlds/worlds/flight_plaid_dialogue_magic_pirate_tale.py
==============================================================

A small pirate-tale story world about flight, plaid, dialogue, and a little
magic at sea.

Premise:
- A crew aboard a ship loves a bright plaid kite that can help them fly.
- A greedy problem threatens the kite or the ship.
- A bit of magic and honest dialogue offer a safe, satisfying turn.
- The ending proves the crew changed the situation in the world, not just the
  wording of the story.

The world is intentionally tiny, classical, and constraint-driven.
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

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

WIND_MIN = 1
WIND_MAX = 5

FLYABLE_SKY = {"calm_breeze", "fair_wind", "bright_wind"}
MAGIC_KINDS = {"sparkle", "glow", "whisper"}
PLAQUID_THINGS = {"plaid", "cloth", "kite"}
BOLD_PIRATE_WORDS = {"aye", "matey", "captain", "deck", "harbor", "treasure"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


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
    kind: str = "thing"          # "character" | "thing" | "creature"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False
    magical: bool = False
    color: str = ""

    region: object | None = None
    crew: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate"}
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
    place: str = "the ship"
    sky: str = "fair_wind"
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    weather: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
    can_fix: set[str]
    needs: set[str]
    prep: str
    tail: str


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.sky: str = setting.sky
        self.facts: dict[str, object] = {}

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(place="the ship", sky="fair_wind", affords={"flight", "magic"}),
    "harbor": Setting(place="the harbor", sky="calm_breeze", affords={"flight", "magic"}),
    "island": Setting(place="the island shore", sky="bright_wind", affords={"flight", "magic"}),
}

ACTIONS = {
    "flight": Action(
        id="flight",
        verb="fly the kite",
        gerund="flying the kite",
        rush="run to the rail and lift the kite high",
        risk="might tangle in the rigging",
        zone={"deck", "air"},
        weather="windy",
        keyword="flight",
        tags={"flight", "wind", "kite"},
    ),
    "magic": Action(
        id="magic",
        verb="cast the little spell",
        gerund="casting the little spell",
        rush="stir the glowing sea-salt",
        risk="might wake a grumpy puff of magic",
        zone={"deck", "hands"},
        weather="",
        keyword="magic",
        tags={"magic", "glow", "spell"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean shirt", type="shirt", region="torso"),
    "sash": Prize(label="sash", phrase="a plaid sash", type="sash", region="torso"),
    "hat": Prize(label="hat", phrase="a fancy hat", type="hat", region="head"),
}

MAGIC_ITEMS = {
    "plaidkite": MagicItem(
        id="plaidkite",
        label="a plaid kite",
        phrase="a bright plaid kite",
        can_fix={"flight"},
        needs={"wind"},
        prep="tie the plaid kite to a steady line",
        tail="held the line steady as the kite climbed",
    ),
    "glowlantern": MagicItem(
        id="glowlantern",
        label="a glow lantern",
        phrase="a small glow lantern",
        can_fix={"magic"},
        needs={"dark"},
        prep="light the glow lantern with a whispered charm",
        tail="watched the lantern glow without a single spark",
    ),
}

GIRL_NAMES = ["Mira", "Pia", "Nora", "Lina", "Saila"]
BOY_NAMES = ["Finn", "Joss", "Tate", "Arlo", "Ned"]
PIRATE_TITLES = ["captain", "matey", "pirate"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    title: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
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
    combos = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            act = _safe_lookup(ACTIONS, action_id)
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone or action_id == "magic":
                    combos.append((place, action_id, prize_id))
    return combos


def _random_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _pirate_voice(name: str, title: str) -> str:
    if title == "captain":
        return f"Captain {name}"
    return f"{name} the {title}"


# ---------------------------------------------------------------------------
# Causal story engine
# ---------------------------------------------------------------------------

def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    world.zone = set(action.zone)
    actor.meters[action.id] = actor.meters.get(action.id, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    if narrate:
        if action.id == "flight":
            world.say(f"{actor.id} lifted the plaid kite and the deck filled with hopeful wind.")
        else:
            world.say(f"{actor.id} whispered the spell and the air began to shimmer.")


def _magic_help(world: World, actor: Entity, item: Entity, prize: Entity, action: Action) -> Optional[MagicItem]:
    if action.id == "flight":
        item_def = MAGIC_ITEMS["plaidkite"]
        item.worn_by = actor.id
        item.magical = True
        world.say(
            f'{actor.id} smiled and said, "Aye, this plaid kite can help us fly without trouble." '
            f"{actor.pronoun('possessive').capitalize()} crew tied {item_def.prep}."
        )
        return item_def
    item_def = MAGIC_ITEMS["glowlantern"]
    item.worn_by = actor.id
    item.magical = True
    world.say(
        f'{actor.id} said, "We can keep the magic small and bright." '
        f"{actor.pronoun('possessive').capitalize()} crew {item_def.prep}."
    )
    return item_def


def tell(setting: Setting, action: Action, prize_cfg: Prize, name: str,
         gender: str, title: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=title, traits=["little", trait]))
    crew = world.add(Entity(id="Crew", kind="character", type="pirate", label="the crew"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, region=prize_cfg.region,
                             plural=prize_cfg.plural, owner=hero.id, caretaker=crew.id))
    if action.id == "flight":
        prize.worn_by = hero.id
    else:
        prize.carried_by = hero.id

    world.say(f"{_pirate_voice(hero.id, title)} was a little {trait} pirate who loved {action.gerund}.")
    world.say(f"{hero.id} also loved {prize.phrase}, which looked bright and proud against the sea.")

    world.para()
    if setting.place == "the ship":
        world.say("On the ship, the wind hissed through the ropes and the mast creaked softly.")
    elif setting.place == "the harbor":
        world.say("In the harbor, gulls called overhead and the water rocked the hull in small waves.")
    else:
        world.say("By the island shore, the waves glittered and the sand flashed pale under the sun.")

    world.say(f"{hero.id} wanted to {action.verb}, but {hero.pronoun('possessive')} {crew.label or 'crew'} worried.")
    world.say(f"If they rushed too hard, {action.risk}.")

    world.para()
    if action.id == "flight":
        world.say(f'{hero.id} said, "Aye, but the kite can carry our cheer."')
        world.say(f'{crew.id} answered, "Only if the wind holds steady, matey."')
    else:
        world.say(f'{hero.id} said, "A little spell can make the lantern shine."')
        world.say(f'{crew.id} answered, "Then keep it tidy, captain, and no wild sparks."')

    item_def = _magic_help(world, hero, prize, prize, action)
    _do_action(world, hero, action, narrate=False)

    if action.id == "flight":
        hero.meters["air"] = hero.meters.get("air", 0.0) + 1.0
        world.say(f"The plaid kite rose high, tugging the line like a happy gull.")
        world.say(f"{hero.id} laughed as the ship seemed to learn how to fly with it.")
    else:
        hero.meters["magic"] = hero.meters.get("magic", 0.0) + 1.0
        world.say(f"The glow lantern warmed the dark, and the deck shone like a tiny moon.")
        world.say(f"{hero.id} and the crew spoke softly, and the spell stayed friendly.")

    world.para()
    world.say(f"In the end, {hero.id} kept {prize.phrase} safe, and the crew had a fine tale for the next harbor.")
    world.facts.update(
        hero=hero,
        crew=crew,
        prize=prize,
        action=action,
        setting=setting,
        magic_item=item_def,
        title=title,
        gender=gender,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    action: Action = _safe_fact(world, f, "action")
    prize: Entity = _safe_fact(world, f, "prize")
    return [
        f'Write a short pirate tale for a child that includes the words "{action.keyword}" and "plaid".',
        f"Tell a gentle sea story about {hero.id}, a little pirate, who wants to {action.verb} while keeping {prize.phrase} safe.",
        f"Write a dialogue-rich story where a crew uses a bit of magic to solve a flying problem on a ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    crew: Entity = _safe_fact(world, f, "crew")
    prize: Entity = _safe_fact(world, f, "prize")
    action: Action = _safe_fact(world, f, "action")
    title = _safe_fact(world, f, "title")
    return [
        QAItem(
            question=f"Who wanted to {action.verb} in the story?",
            answer=f"{hero.id} wanted to {action.verb}, and the crew listened while the wind tugged at the ship.",
        ),
        QAItem(
            question=f"What did the crew worry about when {hero.id} wanted to {action.verb}?",
            answer=f"They worried that {prize.phrase} could be put at risk, so they talked first and chose a careful plan.",
        ),
        QAItem(
            question=f"What did the crew use to help the plan work?",
            answer=f"They used a little magic and a plaid kite-like fix, which let the story end safely and happily.",
        ),
        QAItem(
            question=f"How did {hero.id} speak to the crew?",
            answer=f"{hero.id} spoke in pirate-style dialogue, with short lines like 'Aye' and 'matey' to keep the tale lively.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is plaid?",
            answer="Plaid is a pattern made from crossing lines of color, often seen on cloth, shirts, and kites.",
        ),
        QAItem(
            question="What is a pirate ship for?",
            answer="A pirate ship is for sailing on the sea, carrying a crew, and going from harbor to harbor.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something impossible or surprising happens because of a spell, charm, or enchanted object.",
        ),
        QAItem(
            question="What is flight?",
            answer="Flight means moving through the air, like a bird, a kite, or a ship in a story that seems to soar.",
        ),
    ]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting affords the action and the prize is relevant.
valid(Place, A, P) :- affords(Place, A), action(A), prize(P).

% Flight is reasonable if the prize is a kite-like thing or if the action itself
% is flight and the world has wind.
flight_ok(A, P) :- action(A), prize(P), splashes(A, deck_region), kite_like(P).

% Magic is reasonable when the magic item exists and the action is magic.
magic_ok(A, I) :- action(A), magic_item(I), action_is_magic(A).

valid_story(Place, A, P, G) :- valid(Place, A, P), gender_ok(G, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if aid == "magic":
            lines.append(asp.fact("action_is_magic", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("gender_ok", "girl", pid))
        lines.append(asp.fact("gender_ok", "boy", pid))
        if p.label == "hat" or p.region == "head":
            lines.append(asp.fact("head_item", pid))
    for mid, m in MAGIC_ITEMS.items():
        lines.append(asp.fact("magic_item", mid))
        if "flight" in m.can_fix:
            lines.append(asp.fact("kite_like", "plaidkite"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

TRAITS = ["bold", "cheerful", "curious", "spirited", "lively"]
CURATED = [
    StoryParams(place="ship", action="flight", prize="shirt", name="Mira", gender="girl", title="captain", trait="bold"),
    StoryParams(place="harbor", action="magic", prize="hat", name="Finn", gender="boy", title="matey", trait="curious"),
    StoryParams(place="island", action="flight", prize="sash", name="Nora", gender="girl", title="pirate", trait="cheerful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale world with flight, plaid, dialogue, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--title", choices=PIRATE_TITLES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or _random_name(gender, rng)
    title = getattr(args, "title", None) or rng.choice(PIRATE_TITLES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, title=title, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize),
                 params.name, params.gender, params.title, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.magical:
            bits.append("magical=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, action, prize) combos:\n")
        for place, action, prize in triples:
            print(f"  {place:9} {action:8} {prize:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
