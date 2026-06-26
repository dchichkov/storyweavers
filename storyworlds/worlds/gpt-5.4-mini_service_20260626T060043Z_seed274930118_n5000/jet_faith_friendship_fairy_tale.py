#!/usr/bin/env python3
"""
A fairy-tale storyworld about a little jet, a brave act of faith, and friendship
that helps the day end in a bright new way.

The seed words are "jet" and "faith", and the world is built to keep those ideas
central: a child or young knight cares for a small jet, a friend believes it can
still fly, and the story turns on friendship becoming real help.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    friend: object | None = None
    hero: object | None = None
    jet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "knight", "prince"}:
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
    sky: str
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
class Jet:
    id: str
    label: str
    phrase: str
    nose: str
    tail: str
    launch: str
    weather_safe: set[str]
    needs: set[str]
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
    phrase: str
    kind: str
    helps: set[str]
    worn_region: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    c: object | None = None
    world: object | None = None
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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
class StoryParams:
    place: str
    jet: str
    charm: str
    name: str
    gender: str
    friend: str
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


SETTINGS = {
    "castle_yard": Setting(place="the castle yard", sky="clear", affords={"launch"}),
    "hill": Setting(place="the windy hill", sky="windy", affords={"launch"}),
    "meadow": Setting(place="the meadow", sky="soft", affords={"launch"}),
}

JETS = {
    "silver_jet": Jet(
        id="silver_jet",
        label="silver jet",
        phrase="a little silver jet with bright wings",
        nose="its nose",
        tail="its tail",
        launch="lift off",
        weather_safe={"clear", "windy"},
        needs={"faith", "friendship"},
        tags={"jet", "sky"},
    ),
    "red_jet": Jet(
        id="red_jet",
        label="red jet",
        phrase="a small red jet with a round nose",
        nose="its round nose",
        tail="its tail",
        launch="take off",
        weather_safe={"clear"},
        needs={"faith", "friendship"},
        tags={"jet", "sky"},
    ),
}

CHARMS = {
    "lantern": Charm(
        id="lantern",
        label="lantern",
        phrase="a warm lantern for the watchtower",
        kind="light",
        helps={"faith"},
        worn_region="hand",
        tags={"faith", "light"},
    ),
    "ribbon": Charm(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon from the queen's window",
        kind="gift",
        helps={"friendship"},
        worn_region="hand",
        tags={"friendship"},
    ),
    "crown_pin": Charm(
        id="crown_pin",
        label="crown pin",
        phrase="a little crown pin to keep courage close",
        kind="bravery",
        helps={"faith", "friendship"},
        worn_region="chest",
        tags={"faith", "friendship"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Elin", "Sela", "Ivy"]
BOY_NAMES = ["Oren", "Pip", "Tomas", "Bram", "Eli", "Finn"]
TRAITS = ["gentle", "brave", "curious", "steady", "bright"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_wait_for_faith(world: World) -> list[str]:
    out = []
    hero = _safe_fact(world, world.facts, "hero")
    jet = _safe_fact(world, world.facts, "jet_ent")
    if hero.memes.get("doubt", 0.0) >= THRESHOLD and world.facts.get("friend_believes"):
        sig = ("faith_rises", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["faith"] = hero.memes.get("faith", 0.0) + 1
            out.append(f"{world.facts['friend_ent'].label.capitalize()} stayed by the jet and believed it could still fly.")
    if jet.meters.get("fixed", 0.0) >= THRESHOLD and hero.memes.get("faith", 0.0) >= THRESHOLD:
        sig = ("launch_ready", jet.id)
        if sig not in world.fired:
            world.fired.add(sig)
            jet.meters["ready"] = 1
            out.append("The little jet seemed ready at last.")
    return out


def _r_friendship_help(world: World) -> list[str]:
    out = []
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend_ent")
    jet = _safe_fact(world, world.facts, "jet_ent")
    charm = _safe_fact(world, world.facts, "charm_ent")
    if hero.memes.get("faith", 0.0) >= THRESHOLD and friend.memes.get("friendship", 0.0) >= THRESHOLD:
        sig = ("help", jet.id, charm.id)
        if sig not in world.fired:
            world.fired.add(sig)
            jet.meters["fixed"] = 1
            charm.meters["held"] = 1
            out.append(f"Together, they tied the {charm.label} in place and gave the jet new courage.")
    return out


CAUSAL_RULES = [
    Rule("wait_for_faith", _r_wait_for_faith),
    Rule("friendship_help", _r_friendship_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_launch(world: World, hero: Entity, jet: Entity) -> bool:
    sim = world.copy()
    sim.facts["hero"].memes["doubt"] = 1
    propagate(sim, narrate=False)
    return bool(sim.facts["jet_ent"].meters.get("ready", 0.0) >= THRESHOLD)


def intro(world: World, hero: Entity, friend: Entity, jet: Entity, charm: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, there lived a little {hero.type} named {hero.id} "
        f"who loved {jet.label}s and fair promises."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept {hero.pronoun('possessive')} {jet.label} close, "
        f"because {jet.phrase} felt like a dream that might one day carry a kind heart above the trees."
    )
    world.say(
        f"{friend.id} was {hero.pronoun('possessive')} true friend, and {friend.pronoun()} treasured "
        f"{charm.phrase} for the way it reminded {friend.pronoun('object')} to keep faith."
    )


def arrive(world: World, hero: Entity, friend: Entity, jet: Entity) -> None:
    world.say(
        f"One day, {hero.id} and {friend.id} went to {world.setting.place} where the air was {world.setting.sky}."
    )
    world.say(
        f"{hero.id} wanted the little {jet.label} to {jet.launch}, but a torn wing made the machine still as a sleeping bird."
    )


def worry(world: World, hero: Entity, friend: Entity, jet: Entity, charm: Entity) -> None:
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(
        f"{hero.id} looked at the broken wing and sighed. {hero.pronoun().capitalize()} feared the jet might never rise."
    )
    if predict_launch(world, hero, jet):
        world.say(
            f"But {friend.id} said, \"Have faith. We can help the jet together, and friendship can mend what fear cannot.\""
        )
    else:
        world.say(
            f"But {friend.id} said, \"Have faith. We can still try, and friendship makes a strong pair of hands.\""
        )


def repair(world: World, hero: Entity, friend: Entity, jet: Entity, charm: Entity) -> None:
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} and {friend.id} tied the {charm.label} to the jet's {jet.nose} as a bright sign of trust."
    )
    world.say(
        f"That gentle work made the little machine feel less lonely and more ready to fly."
    )


def launch(world: World, hero: Entity, friend: Entity, jet: Entity, charm: Entity) -> None:
    if jet.meters.get("ready", 0.0) < THRESHOLD:
        pass
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(
        f"At last, the jet {jet.launch}ed into the sky."
    )
    world.say(
        f"{hero.id} waved from the seat while {friend.id} laughed below, and the {charm.label} flashed like a tiny star."
    )
    world.say(
        f"In that moment, the two friends knew that faith had helped their friendship become something strong enough to soar."
    )


def tell(setting: Setting, jet_def: Jet, charm_def: Charm,
         hero_name: str = "Lina", hero_type: str = "girl",
         friend_name: str = "Mira", friend_type: str = "girl",
         trait: str = "gentle") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    jet = world.add(Entity(id=jet_def.id, type="jet", label=jet_def.label, phrase=jet_def.phrase))
    charm = world.add(Entity(id=charm_def.id, type=charm_def.kind, label=charm_def.label, phrase=charm_def.phrase))
    world.facts.update(hero=hero, friend_ent=friend, jet_ent=jet, charm_ent=charm)

    intro(world, hero, friend, jet, charm)
    world.para()
    arrive(world, hero, friend, jet)
    worry(world, hero, friend, jet, charm)
    world.para()
    repair(world, hero, friend, jet, charm)
    launch(world, hero, friend, jet, charm)

    world.facts.update(setting=setting, jet_def=jet_def, charm_def=charm_def, trait=trait)
    return world


def why_story(world: World) -> str:
    f = world.facts
    return (
        f"{f['hero'].id} and {f['friend_ent'].id} are in {f['setting'].place} with "
        f"{f['jet_ent'].label} and {f['charm_ent'].label}. The story turns on faith "
        f"because the jet is broken at first, and friendship matters because the two friends "
        f"repair it together before it can fly."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale for a child about a little jet, faith, and friendship in {f["setting"].place}.',
        f"Tell a gentle story where {f['hero'].id} worries about a jet, but {f['friend_ent'].id} keeps faith and helps.",
        f"Write a fairy-tale ending where a small jet finally flies after friends work together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend_ent")
    jet = _safe_fact(world, f, "jet_ent")
    charm = _safe_fact(world, f, "charm_ent")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {friend.id}, who stayed close as a true friend.",
        ),
        QAItem(
            question=f"What was wrong with the {jet.label} at first?",
            answer=f"The little {jet.label} had a torn wing, so it could not {f['jet_def'].launch} right away.",
        ),
        QAItem(
            question=f"Why did {friend.id} matter in the story?",
            answer=f"{friend.id} mattered because {friend.pronoun()} kept faith, helped repair the jet, and showed real friendship.",
        ),
        QAItem(
            question=f"What did the friends use to help the jet?",
            answer=f"They used the {charm.label}, and that little charm became a sign of their faith in one another.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The jet finally flew, and {hero.id} and {friend.id} felt proud because their friendship helped the day end happily.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "jet": [
        QAItem(
            question="What is a jet?",
            answer="A jet is a kind of airplane that can fly fast through the sky.",
        ),
    ],
    "faith": [
        QAItem(
            question="What is faith?",
            answer="Faith is trust in something or someone, even before you can see the outcome.",
        ),
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between friends who help, share, and stay kind to each other.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set()
    tags.update(world.facts["jet_ent"].meters.keys())
    tags.update(world.facts["jet_def"].tags)
    tags.update(world.facts["charm_def"].tags)
    tags.update({"jet", "faith", "friendship"})
    for tag in ["jet", "faith", "friendship"]:
        out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="castle_yard", jet="silver_jet", charm="lantern", name="Lina", gender="girl", friend="Mira", trait="gentle"),
    StoryParams(place="hill", jet="red_jet", charm="crown_pin", name="Pip", gender="boy", friend="Nora", trait="brave"),
    StoryParams(place="meadow", jet="silver_jet", charm="ribbon", name="Eli", gender="boy", friend="Sela", trait="curious"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for jet_id, jet in JETS.items():
            if "launch" not in setting.affords:
                continue
            for charm_id, charm in CHARMS.items():
                if "faith" in charm.helps or "friendship" in charm.helps:
                    out.append((place, jet_id, charm_id))
    return out


def explain_rejection(jet: Jet, charm: Charm) -> str:
    return f"(No story: {jet.label} and {charm.label} do not make a strong fairy-tale turn together.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a jet, faith, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--jet", choices=JETS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "jet", None) and getattr(args, "charm", None):
        if (getattr(args, "place", None) or "castle_yard", getattr(args, "jet", None), getattr(args, "charm", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "jet", None) is None or c[1] == getattr(args, "jet", None))
              and (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, jet_id, charm_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, jet=jet_id, charm=charm_id, name=name, gender=gender, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(JETS, params.jet), _safe_lookup(CHARMS, params.charm),
                 hero_name=params.name, hero_type=params.gender, friend_name=params.friend, trait=params.trait)
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
place(P) :- setting(P).
compatible(P,J,C) :- setting(P), jet(J), charm(C), affords(P,launch),
                     jet_tag(J,jet), charm_help(C,faith).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for jid, j in JETS.items():
        lines.append(asp.fact("jet", jid))
        lines.append(asp.fact("jet_tag", jid, "jet"))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for h in sorted(c.helps):
            lines.append(asp.fact("charm_help", cid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for combo in asp_valid_combos():
            print(combo)
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.jet} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
