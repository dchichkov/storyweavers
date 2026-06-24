#!/usr/bin/env python3
"""
storyworlds/worlds/reaction_dirt_dim_bomb_humor_pirate_tale.py
===============================================================

A small pirate-tale storyworld about a humorous reaction to a dirt-dim bomb.

Seed tale sketch:
---
On a bright pirate ship, Captain Nia loved shiny things and loud jokes. One day,
the crew found a small bomb-shaped prank canister in the hold. When it popped,
it would spray dirt-dim powder and make everything look gray and dusty for a bit.

Nia wanted to crack it open for fun, but her mate warned that the powder would
ruin the clean map on the table. Nia wrinkled her nose, laughed, and then got a
cloth sack and a splash shield so the crew could enjoy the joke without coating
the map.

World model:
---
- Physical meters: dirtiness, dimness, dustiness, protection, damage.
- Emotional memes: joy, worry, surprise, relief, embarrassment, humor.

The story is generated from world state, not from a frozen template.
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

# -----------------------------------------------------------------------------
# World constants
# -----------------------------------------------------------------------------
THRESHOLD = 1.0



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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    bomb: object | None = None
    gear: object | None = None
    hero: object | None = None
    mate: object | None = None
    prize: object | None = None
    def __post_init__(self):
        for k in ["dirt", "dim", "dust", "damage", "protection"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "surprise", "relief", "embarrassment", "humor"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
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
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Reaction:
    id: str
    verb: str
    gerund: str
    rush: str
    outcome: str
    mess: str
    affects: set[str]
    keyword: str = "reaction"
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
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        c.zone = set(self.zone)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


def _r_soil(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for react in ["dirt", "dim"]:
            if actor.meters[react] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, react)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[react] += 1
                item.meters["damage"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {react}-dim and dusty.")
    return out


def _r_prank(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["surprise"] < THRESHOLD:
            continue
        sig = ("prank", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["humor"] += 1
        out.append(f"The joke tickled the whole crew.")
    return out


CAUSAL_RULES = [_r_soil, _r_prank]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def prize_at_risk(reaction: Reaction, prize: Prize) -> bool:
    return prize.region in reaction.affects


def select_gear(reaction: Reaction, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if reaction.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, reaction: Reaction, prize_id: str) -> dict:
    sim = world.copy()
    _do_reaction(sim, sim.get(actor.id), reaction, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["damage"] >= THRESHOLD)}


def _do_reaction(world: World, actor: Entity, reaction: Reaction, narrate: bool = True) -> None:
    if reaction.id not in world.setting.affords:
        return
    world.zone = set(reaction.affects)
    actor.meters[reaction.mess] += 1
    actor.memes["surprise"] += 1
    actor.memes["humor"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} pirate who loved shiny treasure and silly jokes.")


def likes_reaction(world: World, hero: Entity, reaction: Reaction) -> None:
    world.say(f"{hero.pronoun().capitalize()} liked the silly sound of a {reaction.keyword} and the way it made the deck wobble with laughter.")


def finds_bomb(world: World, hero: Entity, bomb: Entity) -> None:
    world.say(f"One day, {hero.id} found {hero.pronoun('possessive')} {bomb.label} tucked behind a barrel in {world.setting.place}.")


def warns(world: World, mate: Entity, hero: Entity, reaction: Reaction, prize: Entity) -> bool:
    pred = predict_mess(world, hero, reaction, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = reaction.outcome
    world.say(f'"That {reaction.outcome} will ruin your {prize.label}," {mate.label_word} warned with a worried wink.')
    return True


def reacts(world: World, hero: Entity, reaction: Reaction) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} made a face, then laughed anyway. {hero.pronoun().capitalize()} did not want a grumpy bomb to win the day.")
    world.say(f"{hero.pronoun().capitalize()} tried to {reaction.rush}.")


def offer_fix(world: World, mate: Entity, hero: Entity, reaction: Reaction, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(reaction, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=mate.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, reaction, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(f'"How about we {gear_def.prep} first?" {mate.label_word} said. "Then you can enjoy the joke without spoiling the map."')
    return gear_def


def accept(world: World, mate: Entity, hero: Entity, reaction: Reaction, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(f"{hero.id} snorted a laugh and nodded. Soon they {gear_def.tail}.")
    world.say(f"The {reaction.keyword} went off in a harmless puff, and {prize.label} stayed clean while the crew giggled like gulls.")
    world.say(f"{hero.id} ended the day smiling at the messy-turned-silly pirate trick.")


def tell(setting: Setting, reaction: Reaction, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str = "mate") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    mate = world.add(Entity(id="Mate", kind="character", type=parent_type, label="the mate"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=mate.id, region=prize_cfg.region, plural=prize_cfg.plural))
    bomb = world.add(Entity(id="bomb", type="bomb", label="dirt-dim bomb", phrase="a dirt-dim bomb"))

    introduce(world, hero)
    likes_reaction(world, hero, reaction)
    finds_bomb(world, hero, bomb)
    world.para()
    warns(world, mate, hero, reaction, prize)
    reacts(world, hero, reaction)
    world.para()
    gear_def = offer_fix(world, mate, hero, reaction, prize)
    if gear_def:
        accept(world, mate, hero, reaction, prize, gear_def)

    world.facts.update(hero=hero, mate=mate, prize=prize, bomb=bomb, reaction=reaction, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "ship": Setting(place="the ship", affords={"bomb"}),
    "harbor": Setting(place="the harbor", affords={"bomb"}),
    "dock": Setting(place="the dock", affords={"bomb"}),
}

REACTIONS = {
    "bomb": Reaction(
        id="bomb",
        verb="pop the dirt-dim bomb",
        gerund="popping the dirt-dim bomb",
        rush="toss the dirt-dim bomb into the air",
        outcome="dirt-dim",
        mess="dirt",
        affects={"table", "map", "deck"},
        keyword="bomb",
        tags={"bomb", "reaction", "dirt-dim", "humor"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a clean treasure map", type="map", region="table"),
    "hat": Prize(label="hat", phrase="a bright captain's hat", type="hat", region="head"),
}

GEAR = [
    Gear(id="sack", label="a cloth sack", covers={"table"}, guards={"dirt"}, prep="wrap the bomb in a cloth sack", tail="wrapped the bomb in a cloth sack", plural=False),
    Gear(id="cover", label="a splash shield", covers={"table"}, guards={"dirt"}, prep="set up a splash shield", tail="set up the splash shield", plural=False),
]

GIRL_NAMES = ["Nia", "Mara", "Lina", "Tess", "Ruby"]
BOY_NAMES = ["Finn", "Pip", "Jory", "Beck", "Kai"]


@dataclass
class StoryParams:
    place: str
    reaction: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for react_id in setting.affords:
            react = _safe_lookup(REACTIONS, react_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(react, prize) and select_gear(react, prize):
                    combos.append((place, react_id, prize_id))
    return combos


KNOWLEDGE = {
    "bomb": [("What is a bomb?", "A bomb is something that can burst or pop loudly, so people stay careful around it.")],
    "dirt": [("What is dirt?", "Dirt is soil from the ground. It can make hands and clothes look messy.")],
    "dim": [("What does dim mean?", "Dim means not bright. A dim room or object looks darker and less shiny.")],
    "reaction": [("What is a reaction?", "A reaction is what someone does after something happens, like laughing, blinking, or jumping back.")],
    "humor": [("What is humor?", "Humor is when something is funny and makes people smile or laugh.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, reaction = f["hero"], f["prize"], f["reaction"]
    return [
        f'Write a short pirate tale with humor about a {reaction.keyword} and a {prize.label}.',
        f"Tell a funny story where {hero.id} finds a dirt-dim bomb and wants to {reaction.verb}, but {hero.pronoun('possessive')} mate worries about the {prize.label}.",
        f"Write a child-friendly pirate story that includes the words reaction, dirt-dim, and bomb.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, prize, reaction = f["hero"], f["mate"], f["prize"], f["reaction"]
    qa = [
        QAItem(
            question=f"Who found the dirt-dim bomb in {world.setting.place}?",
            answer=f"{hero.id} found it, and {hero.pronoun('possessive')} mate watched carefully."
        ),
        QAItem(
            question=f"Why did the mate worry about the {prize.label}?",
            answer=f"The mate worried because the dirt-dim reaction could make the {prize.label} look dusty and messy."
        ),
        QAItem(
            question=f"What did the crew do so the joke stayed funny?",
            answer=f"They used {f['gear'].label if f.get('gear') else 'a safer plan'} so the bomb could be part of the joke without ruining the {prize.label}."
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and happy, because the pirate prank stayed funny and the {prize.label} stayed clean."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["reaction"].tags)
    out: list[QAItem] = []
    for tag in ["reaction", "bomb", "dirt", "dim", "humor"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", reaction="bomb", prize="map", name="Nia", gender="girl", parent="mate"),
    StoryParams(place="harbor", reaction="bomb", prize="hat", name="Pip", gender="boy", parent="mate"),
]


def explain_rejection(reaction: Reaction, prize: Prize) -> str:
    return f"(No story: this pirate prank would not honestly threaten the {prize.label}, so there is no real caution or fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a humorous dirt-dim bomb reaction.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mate"])
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
    if getattr(args, "reaction", None) and getattr(args, "prize", None):
        react, prize = _safe_lookup(REACTIONS, getattr(args, "reaction", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(react, prize) and select_gear(react, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "reaction", None) is None or c[1] == getattr(args, "reaction", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, reaction, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or "mate"
    return StoryParams(place=place, reaction=reaction, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(REACTIONS, params.reaction), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
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
prize_at_risk(R, P) :- affects(R, X), region(P, X).
protects(G, R, P) :- prize_at_risk(R, P), guards(G, M), reaction_mess(R, M), covers(G, X), region(P, X).
has_fix(R, P) :- protects(_, R, P).
valid_story(Place, R, P) :- affords(Place, R), prize_at_risk(R, P), has_fix(R, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for r in sorted(s.affords):
            lines.append(asp.fact("affords", pid, r))
    for rid, r in REACTIONS.items():
        lines.append(asp.fact("reaction", rid))
        lines.append(asp.fact("reaction_mess", rid, r.mess))
        for x in sorted(r.affects):
            lines.append(asp.fact("affects", rid, x))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
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
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, reaction, prize) combos:\n")
        for place, reaction, prize in triples:
            print(f"  {place:8} {reaction:8} {prize:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
