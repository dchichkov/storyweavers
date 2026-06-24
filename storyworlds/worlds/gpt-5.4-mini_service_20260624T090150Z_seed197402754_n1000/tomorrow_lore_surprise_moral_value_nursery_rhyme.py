#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about tomorrow's lore, with a surprise and a
moral choice.

The domain is intentionally small:
- a child hears a bit of old lore about tomorrow,
- a plain problem appears,
- the child must choose between a silly shortcut and a kind, careful act,
- a surprise ending proves the moral value of the better choice.

This file is self-contained except for the shared Storyweavers result containers
and the shared ASP helper imported lazily when needed.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    child: object | None = None
    h: object | None = None
    parent: object | None = None
    prize: object | None = None
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
    kind: str
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
class Event:
    id: str
    verb: str
    gerund: str
    risk: str
    hazard: str
    zone: set[str]
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
class Help:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def world_copy(world: World) -> World:
    clone = World(world.setting)
    clone.entities = {
        k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            owner=v.owner, caretaker=v.caretaker,
            meters=dict(v.meters), memes=dict(v.memes),
            traits=list(v.traits), plural=v.plural,
        )
        for k, v in world.entities.items()
    }
    clone.fired = set(world.fired)
    clone.paragraphs = [[]]
    return clone


def _rule_tidy(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes.get("chosen_kind", 0) < THRESHOLD:
            continue
        if ent.meters.get("sparkle", 0) < THRESHOLD:
            sig = ("sparkle", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["sparkle"] = 1
            out.append(f"A little sparkle came to {ent.label}.")
    return out


def _rule_mended(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("torn", 0) < THRESHOLD:
            continue
        if ent.memes.get("kind_help", 0) < THRESHOLD:
            continue
        sig = ("mended", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["torn"] = 0
        ent.meters["mended"] = 1
        out.append(f"It grew whole and bright again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_tidy, _rule_mended):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_to_prize(event: Event, prize: Prize) -> bool:
    return prize.region in event.zone


def choose_help(event: Event, prize: Prize) -> Optional[Help]:
    for h in HELPS:
        if event.risk in h.guards and prize.region in h.covers:
            return h
    return None


def predict(world: World, child: Entity, event: Event, prize: Prize) -> dict:
    sim = world_copy(world)
    do_event(sim, sim.get(child.id), event, narrate=False)
    p = sim.get("treasure")
    return {"torn": p.meters.get("torn", 0) >= THRESHOLD}


def rhyme_open(hero: Entity, parent: Entity, setting: Setting, event: Event, prize: Prize) -> None:
    world = hero_world(hero)
    world.say(f"Tomorrow came with a tinkling tune, and {hero.id} heard an old lore by the moon.")
    world.say(f"It whispered of {setting.place}, soft and slow, where little {hero.id} loved to go.")


def hero_world(hero: Entity) -> World:
    return WORLD_REGISTRY[hero.id]


def do_event(world: World, child: Entity, event: Event, narrate: bool = True) -> None:
    child.memes["curious"] = child.memes.get("curious", 0) + 1
    child.meters[event.risk] = child.meters.get(event.risk, 0) + 1
    if narrate:
        world.say(f"{child.id} tried to {event.verb}, and the day turned lively and small.")
    propagate(world, narrate=narrate)


def warning(world: World, parent: Entity, child: Entity, event: Event, prize: Prize) -> bool:
    pred = predict(world, child, event, prize)
    if not pred["torn"]:
        return False
    world.facts["predicted_torn"] = True
    world.say(
        f'"Oh hush, dear heart," said {parent.label}, '
        f'"if you hurry to {event.verb}, your {prize.label} may tear."'
    )
    return True


def surprise(world: World, parent: Entity, child: Entity, event: Event, prize: Prize) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"{child.id} paused in a huff and a puff, then saw a surprise thing: "
        f"a tiny note fluttered from the {setting_word(world.setting)}."
    )


def setting_word(setting: Setting) -> str:
    return setting.kind


def offer_help(world: World, parent: Entity, child: Entity, event: Event, prize: Prize) -> Optional[Help]:
    help_def = choose_help(event, prize)
    if help_def is None:
        return None
    h = world.add(Entity(
        id=help_def.id,
        kind="thing",
        type="thing",
        label=help_def.label,
        owner=child.id,
        caretaker=parent.id,
    ))
    if predict(world, child, event, prize)["torn"]:
        del world.entities[h.id]
        return None
    world.say(
        f"{parent.id} smiled and said, "
        f'"How about we {help_def.prep} and keep our hearts kind?"'
    )
    return help_def


def accept(world: World, parent: Entity, child: Entity, event: Event, prize: Prize, help_def: Help) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["kind_help"] = child.memes.get("kind_help", 0) + 1
    child.memes["chosen_kind"] = 1
    world.say(f"{child.id} chose the kinder way and gave a happy little nod.")
    world.say(
        f"They {help_def.tail}. Then {child.id} could {event.gerund}, "
        f"and the {prize.label} stayed neat and bright."
    )
    propagate(world, narrate=True)


def tell(setting: Setting, event: Event, prize_cfg: Prize,
         hero_name: str = "Mira", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    WORLD_REGISTRY[hero_name] = world

    child = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "curious", "gentle"],
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"
    ))
    prize = world.add(Entity(
        id="treasure", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=child.id, caretaker=parent.id,
        plural=prize_cfg.plural,
    ))

    world.say(f"{child.id} was a little {hero_type} who loved bright whispers and tidy days.")
    world.say(f"{child.id} had {prize.phrase}, and {prize.label} was {hero.pronoun('possessive') if False else 'her'} favorite thing to keep close.")
    world.para()

    world.say(f"One tomorrow morning, {child.id} and {parent.id} went to {setting.place}.")
    world.say(f"{child.id} wanted to {event.verb}, because old lore said it would be fun.")
    warning(world, parent, child, event, prize)
    world.say(f"But {child.id} felt a small surprise in the air and nearly ran ahead anyway.")
    world.say(f"{child.id} stopped, then looked back at {parent.id} with a tiny frown.")
    world.para()

    help_def = offer_help(world, parent, child, event, prize)
    if help_def is not None:
        accept(world, parent, child, event, prize, help_def)

    world.facts.update(
        child=child, parent=parent, prize=prize, event=event,
        setting=setting, help=help_def, resolved=help_def is not None,
    )
    return world


SETTINGS = {
    "garden": Setting(place="the garden", kind="garden", affords={"pick"}),
    "kitchen": Setting(place="the kitchen", kind="kitchen", affords={"stir"}),
    "shore": Setting(place="the shore", kind="shore", affords={"splash"}),
}

EVENTS = {
    "pick": Event(
        id="pick",
        verb="pick the berry patch",
        gerund="picking berries",
        risk="mud",
        hazard="muddy",
        zone={"feet"},
        keyword="tomorrow",
        tags={"tomorrow", "lore"},
    ),
    "stir": Event(
        id="stir",
        verb="stir the honey pot",
        gerund="stirring honey",
        risk="sticky",
        hazard="sticky",
        zone={"hands"},
        keyword="lore",
        tags={"lore"},
    ),
    "splash": Event(
        id="splash",
        verb="splash at the water's edge",
        gerund="splashing by the water",
        risk="wet",
        hazard="wet",
        zone={"feet", "hem"},
        keyword="tomorrow",
        tags={"tomorrow", "lore"},
    ),
}

PRIZES = {
    "crown": Prize(label="crown", phrase="a paper crown", type="crown", region="head"),
    "book": Prize(label="book", phrase="a little storybook", type="book", region="hands"),
    "shawl": Prize(label="shawl", phrase="a soft shawl", type="shawl", region="hem"),
}

HELPS = [
    Help(id="cloth", label="a clean cloth", covers={"hands"}, guards={"sticky"}, prep="wrap our hands in a clean cloth first", tail="wrapped their hands in a clean cloth"),
    Help(id="boots", label="mud boots", covers={"feet"}, guards={"mud"}, prep="put on mud boots first", tail="put on the mud boots"),
    Help(id="cloak", label="a dry cloak", covers={"hem"}, guards={"wet"}, prep="wear a dry cloak first", tail="wore the dry cloak"),
]

GIRL_NAMES = ["Mira", "Nina", "Pia", "Luna", "Tessa", "Wren"]
BOY_NAMES = ["Oli", "Finn", "Ned", "Pip", "Rowan", "Jude"]


WORLD_REGISTRY: dict[str, World] = {}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for eid in setting.affords:
            ev = _safe_lookup(EVENTS, eid)
            for pid, pr in PRIZES.items():
                if risk_to_prize(ev, pr) and choose_help(ev, pr):
                    combos.append((place, eid, pid))
    return combos


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    name: str
    gender: str
    parent: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about tomorrow, lore, surprise, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=EVENTS)
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        ev, pr = _safe_lookup(EVENTS, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (risk_to_prize(ev, pr) and choose_help(ev, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, act, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, event=act, prize=prize, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    ev = _safe_fact(world, f, "event")
    pr = _safe_fact(world, f, "prize")
    return [
        f'Write a short nursery-rhyme story about tomorrow and lore where {child.id} wants to {ev.verb}.',
        f'Write a gentle story for a small child with a surprise ending and a moral choice about {pr.label}.',
        f'Compose a rhyme-like tale in which a parent and {child.id} choose a kind way to handle a risky playtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    prize = _safe_fact(world, f, "prize")
    ev = _safe_fact(world, f, "event")
    qa = [
        QAItem(
            question=f"What did {child.id} want to do at {f['setting'].place}?",
            answer=f"{child.id} wanted to {ev.verb} because the old lore sounded exciting.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because {ev.gerund} could leave the {prize.label} {ev.hazard}.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer="The surprise was that a small kind solution appeared, and it changed the ending from trouble to care.",
        ),
    ]
    if f.get("resolved"):
        help_def = _safe_fact(world, f, "help")
        qa.append(
            QAItem(
                question=f"How did the family keep the {prize.label} safe?",
                answer=f"They used {help_def.label} first, so {child.id} could still enjoy the play without harming the {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"What moral value did {child.id} learn?",
                answer=f"{child.id} learned that being careful and kind can be better than rushing ahead.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    ev = _safe_fact(world, f, "event")
    out: list[QAItem] = [
        QAItem(question="What is lore?", answer="Lore is old knowledge or old stories that people pass along by telling them again and again."),
        QAItem(question="What does tomorrow mean?", answer="Tomorrow means the next day after today."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that makes you pause and notice."),
    ]
    if "tomorrow" in ev.tags:
        out.append(QAItem(question="Why do people talk about tomorrow?", answer="People talk about tomorrow when they mean plans, hopes, or the next day to come."))
    if "lore" in ev.tags:
        out.append(QAItem(question="What can lore do in a story?", answer="Lore can add an old-time feeling and make the story sound like a whisper from before."))
    return out


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


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    event = _safe_lookup(EVENTS, params.event)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    world = tell(setting, event, prize_cfg, params.name, params.gender, params.parent)
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


ASP_RULES = r"""
risk(A,P) :- splashes(A,R), wears_on(P,R).
fix(A,P) :- risk(A,P), event_risk(A,M), help_guards(H,M), help_covers(H,R), wears_on(P,R).
valid(Place,A,P) :- affords(Place,A), risk(A,P), fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, e in EVENTS.items():
        lines.append(asp.fact("event", aid))
        lines.append(asp.fact("event_risk", aid, e.risk))
        for r in sorted(e.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("wears_on", pid, p.region))
    for h in HELPS:
        lines.append(asp.fact("help", h.id))
        for g in sorted(h.guards):
            lines.append(asp.fact("help_guards", h.id, g))
        for c in sorted(h.covers):
            lines.append(asp.fact("help_covers", h.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


CURATED = [
    StoryParams(place="garden", event="pick", prize="crown", name="Mira", gender="girl", parent="mother"),
    StoryParams(place="kitchen", event="stir", prize="book", name="Oli", gender="boy", parent="father"),
    StoryParams(place="shore", event="splash", prize="shawl", name="Luna", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for p, a, pr in triples:
            print(f"  {p:8} {a:8} {pr:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
