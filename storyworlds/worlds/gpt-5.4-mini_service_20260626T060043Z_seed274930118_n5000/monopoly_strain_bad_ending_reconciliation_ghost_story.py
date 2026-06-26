#!/usr/bin/env python3
"""
A small ghost-story world about a monopoly game, a growing strain, a bad ending
that can still become a reconciliation.

The seed premise:
- A child ghost story with a board game and a haunted house mood.
- One character keeps winning too often, creating monopoly and strain.
- The story can end badly, or soften into reconciliation if the right mediation
  happens.

This file follows the Storyweavers contract:
- self-contained stdlib script
- imports shared results eagerly
- lazy imports asp in ASP helpers
- includes registries, parser, parameter resolution, generation, emit, main
- provides inline ASP_RULES plus Python parity checks
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
    carried_by: Optional[str] = None
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mediator: object | None = None
    rival: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    mood: str
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
    room: str
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
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.zone = set(self.zone)
        return w


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def add_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = meter(ent, key) + value


def add_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + value


def show_meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if meter(actor, "monopoly") < THRESHOLD:
            continue
        for other in world.characters():
            if other.id == actor.id:
                continue
            sig = ("strain", actor.id, other.id)
            if sig in world.fired:
                continue
            if meter(other, "hurt") >= THRESHOLD:
                continue
            if meter(other, "strain") >= THRESHOLD:
                continue
            world.fired.add(sig)
            add_meter(other, "strain", 1)
            add_meme(other, "sad", 1)
            out.append(f"The room grew tight, and {other.id} felt the strain of {actor.id}'s winning streak.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("doomed"):
        return out
    hero = _safe_fact(world, world.facts, "hero")
    sig = ("bad_end", hero.id)
    if sig in world.fired:
        return out
    if meter(hero, "strain") >= THRESHOLD or show_meme(hero, "sad") >= THRESHOLD:
        world.fired.add(sig)
        add_meter(hero, "hurt", 1)
        out.append("__bad_ending__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    rival = world.facts.get("rival")
    mediator = world.facts.get("mediator")
    if not hero or not rival:
        return out
    if meter(hero, "monopoly") < THRESHOLD:
        return out
    if meter(rival, "strain") < THRESHOLD and show_meme(rival, "sad") < THRESHOLD:
        return out
    if mediator and meter(mediator, "kindness") < THRESHOLD:
        return out
    sig = ("reconcile", hero.id, rival.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["monopoly"] = 0
    rival.meters["strain"] = 0
    hero.memes["soft"] = hero.memes.get("soft", 0) + 1
    rival.memes["soft"] = rival.memes.get("soft", 0) + 1
    out.append("__reconcile__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_strain, _r_reconcile, _r_bad_ending):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s not in {"__bad_ending__", "__reconcile__"})
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, activity: Activity, prize: Prize, remedy: Remedy,
         hero_name: str, rival_name: str, mediator_name: str,
         hero_type: str = "boy", rival_type: str = "girl", mediator_type: str = "ghost") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["quiet", "greedy"]))
    rival = world.add(Entity(id=rival_name, kind="character", type=rival_type, traits=["gentle", "hurt"]))
    mediator = world.add(Entity(id=mediator_name, kind="character", type=mediator_type, traits=["old", "kind"]))

    world.facts["hero"] = hero
    world.facts["rival"] = rival
    world.facts["mediator"] = mediator
    world.facts["prize"] = prize
    world.facts["activity"] = activity
    world.facts["remedy"] = remedy

    world.say(f"The old house stood quiet in {setting.place}, with a moon-pale hush in every room.")
    world.say(f"{hero.id} loved the {activity.keyword} game, and {hero.pronoun('possessive')} hands moved fastest when the dice rolled.")
    world.say(f"{rival.id} loved it too, but {hero.id} kept taking the biggest prize and calling it {prize.label}.")
    add_meter(hero, "monopoly", 1)
    add_meme(hero, "pride", 1)
    add_meme(rival, "hope", 1)

    world.para()
    world.say(f"At the table, the little board felt like a haunted map, and every turn made the air tighter.")
    world.say(f"{rival.id} wanted a fair turn, but {hero.id} said, \"I should get the whole path.\"")
    add_meter(rival, "strain", 1)
    add_meme(rival, "sad", 1)
    world.facts["doomed"] = True
    propagate(world, narrate=True)

    world.para()
    if meter(rival, "strain") >= THRESHOLD:
        world.say(f"{mediator.id} drifted closer and held out {remedy.label}.")
        world.say(f"\"No one should own the whole game,\" {mediator.id} whispered. \"Try this instead.\"")
        if meter(hero, "monopoly") >= THRESHOLD:
            world.say(f"{hero.id} looked at {rival.id}'s face and felt the strain in the room.")
        if remedy.prep:
            world.say(f"They agreed to {remedy.prep}.")
        if remedy.tail:
            world.say(f"After that, they {remedy.tail}.")
        if meter(hero, "monopoly") >= THRESHOLD:
            hero.meters["monopoly"] = 0
        rival.meters["strain"] = 0
        hero.memes["regret"] = hero.memes.get("regret", 0) + 1
        rival.memes["forgive"] = rival.memes.get("forgive", 0) + 1
        world.facts["doomed"] = False
        world.facts["reconciled"] = True
        propagate(world, narrate=True)
        world.say(f"By the end, the game was shared, the room felt softer, and even the ghostly moon seemed to breathe again.")
    else:
        world.say(f"Nothing changed, and the board stayed cold and lonely.")
        world.say(f"The house kept its bad ending, with nobody smiling at the table.")

    return world


SETTINGS = {
    "old_house": Setting(place="the old house", mood="ghostly", affords={"board_game"}),
    "attic": Setting(place="the attic", mood="dusty", affords={"board_game"}),
    "parlor": Setting(place="the parlor", mood="dim", affords={"board_game"}),
}

ACTIVITIES = {
    "monopoly": Activity(
        id="monopoly",
        verb="play Monopoly",
        gerund="playing Monopoly",
        rush="grab the bank",
        mess="strain",
        soil="more strained",
        keyword="monopoly",
        tags={"monopoly", "game", "board"},
    ),
}

PRIZES = {
    "bank": Prize(
        label="the bank",
        phrase="the bank",
        type="bank",
        room="table",
        plural=False,
    ),
}

REMEDIES = {
    "sharing_rule": Remedy(
        id="sharing_rule",
        label="a sharing rule",
        prep="set the money back in the center and take turns fairly",
        tail="started again with a fair turn for each ghost",
        guards={"strain"},
        helps={"monopoly"},
    ),
    "kind_song": Remedy(
        id="kind_song",
        label="a kind song",
        prep="sing a soft song before the next roll",
        tail="let the room feel lighter before the next move",
        guards={"strain"},
        helps={"monopoly"},
    ),
}

NAMES = ["Mina", "Ned", "Iris", "Otto", "June", "Pip", "Luna", "Rowan"]
GHOST_NAMES = ["Whisp", "Mote", "Hush", "Bramble", "Echo", "Pale", "Nell", "Murmur"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    remedy: str
    hero: str
    rival: str
    mediator: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                for remedy_id in REMEDIES:
                    combos.append((place, act_id, prize_id, remedy_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: monopoly, strain, bad ending, reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--rival")
    ap.add_argument("--mediator")
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
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "remedy", None) is None or c[3] == getattr(args, "remedy", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize, remedy = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    rival = getattr(args, "rival", None) or rng.choice([n for n in NAMES if n != hero])
    mediator = getattr(args, "mediator", None) or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, remedy=remedy, hero=hero, rival=rival, mediator=mediator)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a child where {f["hero"].id} keeps a monopoly on the {f["activity"].keyword} game.',
        f"Tell a spooky but gentle story about strain at the board table, and end with reconciliation if possible.",
        f"Write a moonlit story about a haunted house, a board game, and a fairer way to share the prizes.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    rival = _safe_fact(world, f, "rival")
    mediator = _safe_fact(world, f, "mediator")
    activity = _safe_fact(world, f, "activity")
    remedy = _safe_fact(world, f, "remedy")
    out = [
        QAItem(
            question=f"Who kept taking the biggest prize during the {activity.keyword} game?",
            answer=f"{hero.id} kept taking the biggest prize, so the game began to feel like {hero.pronoun('possessive')} monopoly.",
        ),
        QAItem(
            question=f"Why did {rival.id} feel strain at the table?",
            answer=f"{rival.id} felt strain because {hero.id} would not share the game fairly and kept holding the bank too long.",
        ),
        QAItem(
            question=f"What helped the ghosts reconcile?",
            answer=f"{mediator.id} brought {remedy.label} and helped them share the game again, so the room could soften.",
        ),
    ]
    if world.facts.get("reconciled"):
        out.append(QAItem(
            question="How did the story end?",
            answer="It ended with reconciliation: the game became fairer, the strain eased, and the room no longer felt so cold.",
        ))
    else:
        out.append(QAItem(
            question="How did the story end?",
            answer="It ended badly, with the table still cold and the ghosts unable to make peace.",
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Monopoly?",
            answer="Monopoly is a board game about buying places, collecting money, and trying to win by owning a lot.",
        ),
        QAItem(
            question="What does strain mean?",
            answer="Strain means pressure or tension, like when a room feels tense because people are upset.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace again after a fight or hurt feelings.",
        ),
        QAItem(
            question="Why do ghost stories often feel spooky?",
            answer="Ghost stories often feel spooky because they use quiet places, shadows, old houses, and strange surprises.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this ghost game world only supports the Monopoly strain premise.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        _safe_lookup(REMEDIES, params.remedy),
        params.hero,
        params.rival,
        params.mediator,
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("room", pid, p.room))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for g in sorted(r.guards):
            lines.append(asp.fact("guards", rid, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,A,P,R) :- affords(Place,A), activity(A), prize(P), remedy(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="old_house", activity="monopoly", prize="bank", remedy="sharing_rule", hero="Mina", rival="Ned", mediator="Whisp"),
    StoryParams(place="attic", activity="monopoly", prize="bank", remedy="kind_song", hero="Iris", rival="June", mediator="Murmur"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
