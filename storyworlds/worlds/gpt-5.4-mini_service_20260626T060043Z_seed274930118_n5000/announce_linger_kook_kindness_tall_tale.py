#!/usr/bin/env python3
"""
Standalone storyworld: a tall-tale kindness domain with announce, linger, and kook.

A small town lives beside a windy hill where a kook of a fellow likes to linger
and a child, a baker, or a mayor may announce a kindness challenge. The core
tension is that a loud announcement can stir up trouble if the helper lingers
too long, but kindness can turn a strange scene into a sweet ending.

The world is intentionally compact: a few typed entities, physical meters, and
emotional memes drive a short story with a beginning, a turn, and a resolution.
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
# World model
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
    kind: str = "thing"   # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the hill town"
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
class AnnounceAct:
    id: str
    verb: str
    noun: str
    sound: str
    ripple: str
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
    id: str
    label: str
    phrase: str
    kind: str
    at_risk: str
    plural: bool = False
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    fixes: set[str]
    helps: set[str]
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
        self.trace_notes: list[str] = []

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
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hill_town": Setting(place="the hill town", affords={"announce", "linger", "kindness"}),
    "market": Setting(place="the market square", affords={"announce", "linger", "kindness"}),
    "harbor": Setting(place="the windy harbor", affords={"announce", "linger", "kindness"}),
    "orchard": Setting(place="the apple orchard", affords={"announce", "linger", "kindness"}),
}

ACTIONS = {
    "announce": AnnounceAct(
        id="announce",
        verb="announce",
        noun="announcement",
        sound="a call that rolled over the rooftops",
        ripple="the whole town heard it",
        keyword="announce",
        tags={"announce", "sound"},
    ),
    "linger": AnnounceAct(
        id="linger",
        verb="linger",
        noun="lingering",
        sound="a long pause that stretched like taffy",
        ripple="the crowd grew puzzled",
        keyword="linger",
        tags={"linger", "pause"},
    ),
    "kook": AnnounceAct(
        id="kook",
        verb="call the kook",
        noun="kook",
        sound="a whistling shout with a silly twist",
        ripple="a kooky fellow came ambling along",
        keyword="kook",
        tags={"kook", "silly"},
    ),
}

PRIZES = {
    "bell": Prize(
        id="bell",
        label="brass bell",
        phrase="a bright brass bell",
        kind="bell",
        at_risk="noise",
        tags={"bell", "sound"},
    ),
    "banner": Prize(
        id="banner",
        label="kindness banner",
        phrase="a long kindness banner",
        kind="banner",
        at_risk="wind",
        tags={"kindness", "cloth"},
    ),
    "cake": Prize(
        id="cake",
        label="celebration cake",
        phrase="a tall celebration cake",
        kind="cake",
        at_risk="crowd",
        tags={"cake", "sweet"},
    ),
    "lantern": Prize(
        id="lantern",
        label="paper lantern",
        phrase="a paper lantern with a gold fringe",
        kind="lantern",
        at_risk="rain",
        tags={"light", "paper"},
    ),
}

GEAR = [
    Gear(
        id="rope",
        label="a sturdy rope",
        prep="tie the banner to a sturdy rope first",
        tail="tied the banner down with a sturdy rope",
        fixes={"wind"},
        helps={"banner"},
    ),
    Gear(
        id="cloth",
        label="a rain cloth",
        prep="cover the lantern with a rain cloth first",
        tail="covered the lantern with a rain cloth",
        fixes={"rain"},
        helps={"lantern"},
    ),
    Gear(
        id="tray",
        label="a flat cake tray",
        prep="set the cake on a flat tray first",
        tail="set the cake on a flat tray",
        fixes={"crowd"},
        helps={"cake"},
    ),
    Gear(
        id="felt",
        label="soft felt pads",
        prep="hang the bell on soft felt pads first",
        tail="hung the bell on soft felt pads",
        fixes={"noise"},
        helps={"bell"},
    ),
]

NAMES = ["Milo", "Nora", "Elsie", "Otis", "Benny", "June", "Ivy", "Toby"]
KINDS = ["girl", "boy"]
PARENTS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["cheerful", "bold", "gentle", "bright-eyed", "sturdy", "quick", "kind"]


@dataclass
class StoryParams:
    setting: str
    action: str
    prize: str
    name: str
    kind: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def prize_at_risk(action: AnnounceAct, prize: Prize) -> bool:
    return prize.at_risk in {"wind", "rain", "noise", "crowd"} and (
        (action.id == "announce" and prize.kind in {"bell", "banner", "lantern"})
        or (action.id == "linger" and prize.kind in {"cake", "lantern", "banner"})
        or (action.id == "kook" and prize.kind in {"bell", "cake", "banner"})
    )


def select_gear(action: AnnounceAct, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.kind in gear.helps and prize.at_risk in gear.fixes:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for action_id in setting.affords:
            action = _safe_lookup(ACTIONS, action_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(action, prize) and select_gear(action, prize):
                    combos.append((setting_id, action_id, prize_id))
    return combos


def explain_rejection(action: AnnounceAct, prize: Prize) -> str:
    return (
        f"(No story: the {action.keyword} idea and the {prize.label} do not make a "
        f"good tall-tale problem together. The trouble would not honestly grow, "
        f"so there would be no real turn to resolve.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, helper: Entity, prize: Entity, action: AnnounceAct) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} who loved a good tall tale, "
        f"especially one that began with a big {action.verb}."
    )
    world.say(
        f"People said {helper.id} was a kook of a helper, because {helper.pronoun()} "
        f"could {action.verb} once and then linger like a shadow on a fence post."
    )
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    helper.memes["kook"] = helper.memes.get("kook", 0) + 1
    prize.meters["shine"] = prize.meters.get("shine", 0) + 1


def setup(world: World, hero: Entity, helper: Entity, prize: Entity, action: AnnounceAct) -> None:
    world.para()
    world.say(
        f"On a blustery morning at {world.setting.place}, {hero.id} heard "
        f"that {helper.id} planned to {action.verb} a kindness for the whole town."
    )
    world.say(
        f"The prize was {prize.phrase}, and the wind was already nosing at it."
    )
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1


def predict_trouble(world: World, hero: Entity, action: AnnounceAct, prize: Entity) -> dict:
    sim = world.copy()
    perform_action(sim, sim.get(hero.id), action, narrate=False)
    pr = sim.entities[prize.id]
    return {
        "soiled": pr.meters.get("broken", 0) > 0 or pr.meters.get("scattered", 0) > 0,
        "puzzle": sim.facts.get("puzzle", 0),
    }


def perform_action(world: World, actor: Entity, action: AnnounceAct, narrate: bool = True) -> None:
    sig = ("act", actor.id, action.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if action.id == "announce":
        actor.memes["boldness"] = actor.memes.get("boldness", 0) + 1
        if narrate:
            world.say(f"{actor.id} lifted a hand and announced kindness with a voice like a brass trumpet.")
            world.say(f"{action.sound.capitalize()}, and {action.ripple}.")
    elif action.id == "linger":
        actor.memes["puzzlement"] = actor.memes.get("puzzlement", 0) + 1
        if narrate:
            world.say(f"{actor.id} did not hurry; {action.sound}, and {action.ripple}.")
    elif action.id == "kook":
        actor.memes["kook"] = actor.memes.get("kook", 0) + 1
        if narrate:
            world.say(f"{actor.id} gave a kooky call; {action.sound}, and {action.ripple}.")


def trouble(world: World, hero: Entity, helper: Entity, prize: Entity, action: AnnounceAct) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["linger"] = helper.memes.get("linger", 0) + 1
    world.say(
        f"But the trouble was plain: if {helper.id} kept trying to {action.verb}, "
        f"the wind and the crowd would jostle {prize.pronoun('possessive')} prize."
    )
    if action.id == "linger":
        world.say(f"{helper.id} kept lingering anyway, like a mule with a tune in its ear.")


def warn(world: World, hero: Entity, helper: Entity, prize: Entity, action: AnnounceAct) -> None:
    world.say(
        f'{hero.id} said, "That may be a fine idea, but this wind has long hands and '
        f'it will grab at {prize.pronoun("possessive")} prize."'
    )
    world.facts["warned"] = True
    world.facts["risk"] = action.ripple


def change_mind(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["softened"] = helper.memes.get("softened", 0) + 1
    world.say(
        f"{helper.id} blinked, scratched {helper.pronoun('possessive')} head, and looked at "
        f"{hero.id} as if a lantern had lit inside {helper.pronoun('possessive')} chest."
    )


def compromise(world: World, helper: Entity, prize: Entity, action: AnnounceAct) -> Optional[Gear]:
    gear = select_gear(action, prize)
    if not gear:
        return None
    if ("gear", gear.id, prize.id) in world.fired:
        return gear
    world.fired.add(("gear", gear.id, prize.id))
    world.say(
        f"Then {helper.id} found a kinder fix: {gear.prep}, so the old trouble could not grab it."
    )
    world.facts["gear"] = gear
    return gear


def resolve(world: World, hero: Entity, helper: Entity, prize: Entity, action: AnnounceAct, gear: Gear) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 2
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} grinned so wide it looked like sunrise on the riverbank."
    )
    world.say(
        f'Together they {gear.tail}, and then {helper.id} could {action.verb} the kindness without a hitch.'
    )
    world.say(
        f"By the last sentence of the day, {prize.id} stayed safe, the wind lost its grip, "
        f"and the town had a story big enough to stretch from the bakery to the bell tower."
    )


def tell(setting: Setting, action: AnnounceAct, prize_cfg: Prize, hero_name: str,
         hero_kind: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_kind,
        traits=["little", trait],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="person",
        traits=["kook", "kind"],
    ))
    prize = world.add(Entity(
        id=prize_cfg.label,
        kind="thing",
        type=prize_cfg.kind,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
    ))

    intro(world, hero, helper, prize, action)
    setup(world, hero, helper, prize, action)
    world.para()
    perform_action(world, helper, action)
    trouble(world, hero, helper, prize, action)
    warn(world, hero, helper, prize, action)
    change_mind(world, helper, hero)
    gear = compromise(world, helper, prize, action)
    if gear:
        world.para()
        resolve(world, hero, helper, prize, action, gear)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        action=action,
        gear=gear,
        setting=setting,
        resolved=gear is not None,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A prize is at risk if an action and prize are a plausible tall-tale mismatch.
at_risk(A, P) :- action(A), prize(P), risk(A, P).

% A gear item is a compatible fix only when it actually matches the problem.
fixes(G, A, P) :- gear(G), at_risk(A, P), helps(G, P), fixes_risk(G, R), risk_of(A, R).

valid(Setting, A, P) :- affords(Setting, A), at_risk(A, P), has_fix(A, P).

has_fix(A, P) :- fixes(_, A, P).

valid_story(Setting, A, P, Kind) :- valid(Setting, A, P), wears(Kind, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk_of", aid, "wind" if aid in {"linger", "kook"} else "noise"))
        if aid == "announce":
            lines.append(asp.fact("risk_of", aid, "wind"))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("wears", "any", pid))
        lines.append(asp.fact("risk", "announce", pid) if pid in {"banner", "bell", "lantern"} else asp.fact("risk", "linger", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for p in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, p))
        for r in sorted(g.fixes):
            lines.append(asp.fact("fixes_risk", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall-tale story for a child that includes the words "{f["action"].keyword}", "kindness", and "{f["helper"].id}".',
        f"Tell a funny but gentle story where {f['helper'].id} wants to {f['action'].verb} while {f['hero'].id} worries about {f['prize'].phrase}.",
        f"Write a story with a big announcement, a long linger, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    prize: Entity = _safe_fact(world, f, "prize")
    action: AnnounceAct = _safe_fact(world, f, "action")
    gear: Optional[Gear] = f.get("gear")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.traits[-1]} {hero.type}, and {helper.id}, the kooky helper."
        ),
        QAItem(
            question=f"What did {helper.id} want to do?",
            answer=f"{helper.id} wanted to {action.verb} a kindness, but that first caused trouble for {prize.phrase}."
        ),
        QAItem(
            question=f"Why did {hero.id} worry about the prize?",
            answer=(
                f"{hero.id} worried because the wind and crowd could jostle {prize.phrase}. "
                f"The story turned when everyone chose a safer way."
            ),
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"What helped the ending work out?",
                answer=(
                    f"{gear.label} helped because it matched the problem and kept {prize.label} safe "
                    f"while {helper.id} still got to {action.verb}."
                ),
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone helps, shares, or speaks gently so another person feels safe and cared for.",
        )
    ],
    "kook": [
        QAItem(
            question="What does kooky mean?",
            answer="Kooky means a little odd or silly in a way that can make people smile.",
        )
    ],
    "announce": [
        QAItem(
            question="What does it mean to announce something?",
            answer="To announce something means to say it out loud so other people can hear it clearly.",
        )
    ],
    "linger": [
        QAItem(
            question="What does linger mean?",
            answer="To linger means to stay in one place a little longer instead of hurrying away.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["action"].keyword, "kindness", "kook"}
    out: list[QAItem] = []
    for tag in ["announce", "linger", "kook", "kindness"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE.get(tag, []))
    return out


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
        lines.append(f"  {e.id:12} ({e.kind:8} {e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="hill_town", action="announce", prize="banner", name="Milo", kind="boy", helper="Aunt Tess", trait="bold"),
    StoryParams(setting="market", action="linger", prize="cake", name="Nora", kind="girl", helper="Uncle Pip", trait="bright-eyed"),
    StoryParams(setting="harbor", action="kook", prize="lantern", name="Otis", kind="boy", helper="Grandma Wren", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale kindness storyworld with announce, linger, and kook.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--action", choices=ACTIONS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--helper")
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
    if getattr(args, "action", None) and getattr(args, "prize", None):
        act, prize = _safe_lookup(ACTIONS, getattr(args, "action", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, action, prize = rng.choice(list(combos))
    kind = getattr(args, "kind", None) or rng.choice(KINDS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["Aunt Tess", "Uncle Pip", "Grandma Wren", "Mayor Dot"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, action=action, prize=prize, name=name, kind=kind, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(ACTIONS, params.action),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.kind,
        params.helper,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, action, prize) combos ({len(stories)} with kind):\n")
        for setting, action, prize in triples:
            kinds = sorted(g for (s, a, p, g) in stories if (s, a, p) == (setting, action, prize))
            print(f"  {setting:10} {action:8} {prize:10}  [{', '.join(kinds)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
