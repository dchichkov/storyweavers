#!/usr/bin/env python3
"""
A standalone storyworld: a tiny adventure in a toy library, where necessity,
a pocket, and a die matter, and magic and reconciliation create the turn.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    pocket: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man"}
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
    place: str = "the toy library"
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
    verb: str
    gerund: str
    urgency: str
    risk: str
    twist: str
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
    region: str = "hand"
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
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
        self.trace: list[str] = []

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
            self.trace.append(text)

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
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "toy_library": Setting(place="the toy library", affords={"search", "magic"}),
}

QUESTS = {
    "necessity": Quest(
        id="necessity",
        verb="find the necessary clue",
        gerund="finding the necessary clue",
        urgency="needed",
        risk="the clue could vanish",
        twist="the clue was hidden where no one expected",
        keyword="necessity",
        tags={"necessity", "need"},
    ),
    "pocket": Quest(
        id="pocket",
        verb="check the pocket",
        gerund="checking pockets",
        urgency="careful",
        risk="the pocket might hold the wrong thing",
        twist="the pocket belonged to a stuffed fox",
        keyword="pocket",
        tags={"pocket", "hide"},
    ),
    "die": Quest(
        id="die",
        verb="roll the die",
        gerund="rolling a die",
        urgency="bold",
        risk="the die could tumble away",
        twist="the die answered with a glowing path",
        keyword="die",
        tags={"die", "magic"},
    ),
}

PRIZES = {
    "map": Prize(id="map", label="map", phrase="a folded treasure map"),
    "key": Prize(id="key", label="key", phrase="a tiny brass key"),
    "book": Prize(id="book", label="book", phrase="a storybook with a blue ribbon"),
}

GEAR = {
    "pouch": Gear(
        id="pouch",
        label="a little cloth pouch",
        prep="put the die in a little cloth pouch first",
        tail="slipped the die into the pouch and tied it shut",
        guards={"die"},
    ),
    "glove": Gear(
        id="glove",
        label="soft mittens",
        prep="put on soft mittens first",
        tail="wore the mittens and kept the key safe",
        guards={"key"},
    ),
}

GIRL_NAMES = ["Lina", "Mina", "Pia", "Nora", "Tia", "Iris"]
BOY_NAMES = ["Milo", "Toby", "Arlo", "Eli", "Ned", "Jude"]
TRAITS = ["curious", "brave", "gentle", "inventive", "lively"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP
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


ASP_RULES = r"""
quest_at_risk(Q) :- quest(Q), needs(Q, Need), risk(Need).
compatible(G, Q) :- gear(G), quest(Q), guards(G, Q).
valid_story(S, Q, P, Gender) :- setting(S), quest(Q), prize(P), gear_ok(Q), wears(Gender, P).
gear_ok(Q) :- compatible(_, Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs", qid, q.keyword))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for tag in sorted(g.guards):
            lines.append(asp.fact("guards", gid, tag))
    for g in ["girl", "boy"]:
        for pid in PRIZES:
            lines.append(asp.fact("wears", g, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def quest_needs_gear(q: Quest) -> bool:
    return any(g for g in GEAR.values() if q.id in g.guards)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for q in QUESTS:
            for p in PRIZES:
                if quest_needs_gear(_safe_lookup(QUESTS, q)):
                    out.append((s, q, p))
    return out


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _act(world: World, hero: Entity, quest: Quest, prize: Entity, narrate: bool = True) -> None:
    if quest.id not in world.setting.affords:
        pass
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    if narrate:
        world.say(f"{hero.pronoun().capitalize()} tried to {quest.verb} near the shelves.")
    if quest.id == "die":
        hero.memes["magic"] = hero.memes.get("magic", 0.0) + 1
        prize.meters["glow"] = prize.meters.get("glow", 0.0) + 1


def predict(world: World, hero: Entity, quest: Quest, prize: Entity) -> dict:
    sim = world.copy()
    _act(sim, sim.get(hero.id), quest, sim.get(prize.id), narrate=False)
    return {
        "glow": sim.get(prize.id).meters.get("glow", 0.0),
        "tension": sim.get(hero.id).memes.get("tension", 0.0),
    }


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.label} who loved the toy library's quiet corners.")


def setup(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    world.say(
        f"{hero.id} came to {world.setting.place} with {hero.pronoun('possessive')} {helper.label}."
    )
    world.say(
        f"{hero.id} needed a {quest.keyword} clue for the journey ahead, and {hero.pronoun()} kept "
        f"thinking about {prize.phrase}."
    )


def tension(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["tension"] = hero.memes.get("tension", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {quest.verb}, but {helper.id} warned that {quest.risk}."
    )
    world.say(
        f'"It is a matter of necessity," {helper.pronoun()} said, "or the search could die out before it begins."'
    )


def twist_and_reconcile(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> Optional[Gear]:
    if quest.id == "pocket":
        world.say(
            f"Then came the twist: the pocket belonged to a stuffed fox on the reading bench."
        )
        world.say(
            f"Inside that pocket, they found the clue at once, and {hero.id} stopped frowning."
        )
        hero.memes["tension"] = 0.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        return None

    if quest.id == "die":
        gear = GEAR["pouch"]
        world.say(
            f"Then the magic die began to shine, and a ribbon of light pointed toward a hidden shelf."
        )
        world.say(
            f'{helper.id} smiled and said, "Let us use the pouch first."'
        )
        return gear

    world.say(
        f"Twist: the clue was not on the shelf at all. It was tucked into a pocket in an old toy coat."
    )
    return None


def conclude(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity, gear: Optional[Gear]) -> None:
    if gear:
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        hero.memes["tension"] = 0.0
        world.say(
            f"{hero.id} agreed, and soon {gear.tail}. Together they followed the glowing path and found {prize.phrase}."
        )
        world.say(
            f"At the end, {hero.id} laughed with {helper.id}, and the toy library felt safe and bright again."
        )
    elif quest.id == "pocket":
        world.say(
            f"{hero.id} and {helper.id} shared a grin, because the fox's pocket made the whole mystery easy to solve."
        )
        world.say(
            f"By the end, they carried the clue home and the library's little adventure was complete."
        )
    else:
        world.say(
            f"{hero.id} took a deep breath, and the promise of the next page felt enough for the day."
        )
        world.say(
            f"The toy library stood quiet behind them, but the path ahead felt brighter."
        )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, hero_gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=f"{trait} explorer"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="library keeper"))
    prize = world.add(Entity(id=prize_cfg.id, type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase))

    introduce(world, hero)
    world.para()
    setup(world, hero, helper, quest, prize)
    tension(world, hero, helper, quest, prize)
    _act(world, hero, quest, prize, narrate=True)
    world.para()
    gear = twist_and_reconcile(world, hero, helper, quest, prize)
    conclude(world, hero, helper, quest, prize, gear)

    world.facts.update(hero=hero, helper=helper, prize=prize, quest=quest, gear=gear, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Content / QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    return [
        f'Write an adventure story for a young child in {world.setting.place} with the word "{quest.keyword}".',
        f"Tell a story where {hero.id} must face a necessity, notice a pocket, and use a die to solve a problem.",
        f"Write a gentle toy-library tale with magic, a twist, and reconciliation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    quest = _safe_fact(world, f, "quest")
    prize = _safe_fact(world, f, "prize")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Where does {hero.id} go in the story?",
            answer=f"{hero.id} goes to {world.setting.place} with the library keeper.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id} about the adventure?",
            answer=f"{helper.id} warned {hero.id} because {quest.risk}. The warning was about necessity, so the search would not fail.",
        ),
        QAItem(
            question=f"What made the story turn magical?",
            answer=f"The magic die began to glow and pointed the way, so the search changed from worry into a hopeful chase.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a pocket?",
            answer="A pocket is a small sewn opening in clothes where tiny things can be carried safely.",
        ),
        QAItem(
            question="What is a die?",
            answer="A die is a small cube with spots on its sides that people can roll in games.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something special or impossible in real life happens in the story, like a glowing die or a light that shows the way.",
        ),
    ]
    if f["quest"].id == "pocket":
        out.append(
            QAItem(
                question="What was special about the pocket in the twist?",
                answer="The pocket belonged to a stuffed fox, and that unexpected hiding place solved the mystery.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="toy_library", quest="die", prize="key", name="Mina", gender="girl", helper="librarian", trait="curious"),
    StoryParams(setting="toy_library", quest="pocket", prize="map", name="Milo", gender="boy", helper="librarian", trait="brave"),
    StoryParams(setting="toy_library", quest="necessity", prize="book", name="Lina", gender="girl", helper="librarian", trait="inventive"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld in a toy library.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["librarian"])
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
    combos = valid_combos()
    if getattr(args, "setting", None) or getattr(args, "quest", None) or getattr(args, "prize", None):
        combos = [
            c for c in combos
            if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
            and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
            and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or "librarian"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(QUESTS, params.quest), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.helper, params.trait)
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


# ---------------------------------------------------------------------------
# ASP verify / parity
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible story patterns:")
        for item in combos:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                p = resolve_params(args, rng)
            except StoryError:
                continue
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
            header = f"### {p.name}: {p.quest} in {p.setting} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
