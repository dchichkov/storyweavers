#!/usr/bin/env python3
"""
A standalone storyworld for a cautionary tall tale about a wallaby, creme, and powder.

Premise:
A proud wallaby loves a fancy creme powder used for making puffs and sweets look bright.
The wallaby wants to shake the powder everywhere, but a careful keeper warns that the powder can spill, puff, and turn the room into a sneezy cloud.

Turn:
The wallaby ignores the warning, stamps into the pantry, and sends the powder flying.
That makes a tall, funny mess and coats the floor, the whisk, and the wallaby's paws.

Resolution:
The wallaby helps clean up, learns to use only a tiny spoonful, and saves the rest in a sealed tin.
The ending image proves the change: the powder stays calm, the pantry stays neat, and the wallaby chooses careful fun instead of wild mischief.
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
    kind: str = "thing"  # "character" | "thing"
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

    region: object | None = None
    floor: object | None = None
    hero: object | None = None
    keeper: object | None = None
    prize: object | None = None
    wallaby_paws: object | None = None
    whisk: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"wallaby"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"keeper", "cook", "adult"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    indoors: bool
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
    mess: str
    soil: str
    zone: set[str]
    keyword: str
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
        return any(region in getattr(g, "covers", set()) for g in self.worn_items(actor) if g.id in self.entities)

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("powder", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.kind == "character":
                continue
            if item.id == "powder_tin":
                continue
            if item.worn_by == actor.id:
                continue
            if item.type not in {"floor", "whisk", "shelf", "paw"}:
                continue
            if item.id in {"floor"} or item.type in {"whisk", "shelf"} or item.id == "wallaby_paws":
                sig = ("spill", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["powder"] = item.meters.get("powder", 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"The creme powder blew over {item.label or item.type}.")
    return out


def _r_sneeze(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("powder", 0.0) < THRESHOLD:
            continue
        sig = ("sneeze", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["shock"] = actor.memes.get("shock", 0.0) + 1
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.id} snorted in the powdery air and got a worried look.")
    return out


CAUSAL_RULES = [
    _r_spill,
    _r_sneeze,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_mess(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "powder_cloud": actor.meters.get("powder", 0.0) >= THRESHOLD,
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        return
    world.zone = set(action.zone)
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1
    actor.memes["boldness"] = actor.memes.get("boldness", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "proud")
    world.say(f"{hero.id} was a little {trait} wallaby with a nose for shiny things.")


def loves(world: World, hero: Entity, action: Action) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {action.gerund}, and {action.keyword} made the room feel grand and fancy.")


def arrives(world: World, hero: Entity, keeper: Entity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {keeper.label_word} were in {world.setting.place}.")
    world.say("The shelves were tall, the tins were neat, and the air smelled sweet and dusty.")


def wants(world: World, hero: Entity, action: Action, prize: Entity) -> None:
    world.say(f"{hero.id} wanted to {action.verb}, but {hero.pronoun('possessive')} eyes kept wandering to the {prize.label}.")


def warn(world: World, keeper: Entity, hero: Entity, action: Action, prize: Entity) -> None:
    pred = predict_mess(world, hero, action, prize.id)
    if pred["soiled"]:
        world.say(f'"Careful," {keeper.label_word} said. "That {prize.label} can go everywhere if you shake it too hard."')


def defy(world: World, hero: Entity, action: Action) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} did not listen.")
    world.say(f"{hero.pronoun().capitalize()} tried to {action.rush}, and the whole pantry seemed to hold its breath.")


def spill_and_mess(world: World, hero: Entity) -> None:
    hero.meters["powder"] = hero.meters.get("powder", 0.0) + 1
    propagate(world, narrate=True)


def apology(world: World, hero: Entity, keeper: Entity, prize: Entity) -> None:
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1
    world.say(f"Then {hero.id} saw the white cloud on the floor and felt small inside.")
    world.say(f'"I made a big mess," {hero.id} said. "{keeper.label_word}, I will help fix the creme powder now."')


def clean_up(world: World, hero: Entity, keeper: Entity, prize: Entity, gear: Gear) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    hero.meters["powder"] = 0.0
    prize.meters["dirty"] = 0.0
    world.say(f"{keeper.label_word} gave {hero.id} a soft brush and a small spoon.")
    world.say(f"Together they used {gear.label}, swept the powder back into the tin, and kept only a tiny pinch for later.")
    world.say(f"In the end, {hero.id} was {action_safe_phrase(prize)} and the pantry was calm again.")


def action_safe_phrase(prize: Entity) -> str:
    return f"the {prize.label} stayed sealed"


SETTINGS = {
    "pantry": Setting(place="the pantry", indoors=True, affords={"shake", "sift"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"shake", "decorate"}),
    "market": Setting(place="the market stall", indoors=False, affords={"carry"}),
}

ACTIONS = {
    "shake": Action(
        id="shake",
        verb="shake the creme powder",
        gerund="shaking the creme powder",
        rush="shake the tin high and hard",
        mess="powder",
        soil="covered in powder",
        zone={"floor", "paw", "whisk"},
        keyword="creme powder",
    ),
    "sift": Action(
        id="sift",
        verb="sift the creme powder",
        gerund="sifting the creme powder",
        rush="tip the sieve too fast",
        mess="powder",
        soil="dusty with powder",
        zone={"floor", "paw", "whisk"},
        keyword="creme powder",
    ),
    "decorate": Action(
        id="decorate",
        verb="decorate the cakes with creme powder",
        gerund="decorating cakes with creme powder",
        rush="fling the powder in a big swirl",
        mess="powder",
        soil="dusted with powder",
        zone={"paw", "floor"},
        keyword="creme powder",
    ),
    "carry": Action(
        id="carry",
        verb="carry the creme powder tin",
        gerund="carrying the creme powder tin",
        rush="bounce the tin along the path",
        mess="powder",
        soil="spilled powder",
        zone={"paw"},
        keyword="creme powder",
    ),
}

PRIZES = {
    "tin": Prize(label="tin", phrase="a bright tin of creme powder", type="tin", region="paw"),
}

GEAR = [
    Gear(
        id="lid",
        label="a snug lid",
        covers={"paw"},
        guards={"powder"},
        prep="close the tin with a snug lid first",
        tail="closed the tin with a snug lid",
    ),
    Gear(
        id="spoon",
        label="a small spoon",
        covers={"paw"},
        guards={"powder"},
        prep="use a small spoon instead",
        tail="used a small spoon instead",
    ),
]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str = "Wally"
    seed: Optional[int] = None
    CURATED: list = field(default_factory=list)
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


class WorldFacts:
    pass


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            for prize in PRIZES:
                combos.append((place, action, prize))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "action")
    prize = _safe_fact(world, f, "prize")
    return [
        'Write a short cautionary tall tale about a wallaby, creme, and powder.',
        f"Tell a funny warning story where {hero.id} tries to {act.verb} and almost ruins {prize.phrase}.",
        f"Write a child-friendly tall tale that ends with {hero.id} learning to handle the creme powder carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    keeper = _safe_fact(world, f, "keeper")
    act = _safe_fact(world, f, "action")
    prize = _safe_fact(world, f, "prize")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little wallaby who wanted the creme powder.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the creme powder?",
            answer=f"{hero.id} wanted to {act.verb}, but that was too wild for the pantry.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} learned to use a small spoon, keep the tin closed, and leave {prize.label} neat while {keeper.label_word} watched with a smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is creme powder?",
            answer="Creme powder is a soft, fine powder that can puff into the air if it is shaken too hard.",
        ),
        QAItem(
            question="Why can powder be messy?",
            answer="Powder can be messy because tiny bits spread quickly and can cover floors, paws, and tools.",
        ),
        QAItem(
            question="What is a wallaby?",
            answer="A wallaby is a small hopping animal with strong back legs and a long tail.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str = "Wally") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="wallaby", traits=["little", "proud", "curious"]))
    keeper = world.add(Entity(id="Keeper", kind="character", type="keeper", label="the keeper"))
    prize = world.add(Entity(id="creme_tin", type=prize_cfg.type, label="creme powder", phrase=prize_cfg.phrase, owner=hero.id, caretaker=keeper.id, region=prize_cfg.region))

    floor = world.add(Entity(id="floor", type="floor", label="the floor"))
    whisk = world.add(Entity(id="whisk", type="whisk", label="the whisk"))
    wallaby_paws = world.add(Entity(id="wallaby_paws", type="paw", label="the wallaby's paws"))
    _ = (floor, whisk, wallaby_paws)

    introduce(world, hero)
    loves(world, hero, action)
    world.say(f"{keeper.label_word} kept a bright tin of {prize.label} on the shelf.")
    world.say(f"{hero.id} loved its creamy smell and the fancy look it gave to cakes.")

    world.para()
    arrives(world, hero, keeper)
    wants(world, hero, action, prize)
    warn(world, keeper, hero, action, prize)
    defy(world, hero, action)
    spill_and_mess(world, hero)

    world.para()
    apology(world, hero, keeper, prize)
    gear = GEAR[0]
    world.say(f"{keeper.label_word} showed {hero.id} {gear.prep}.")
    hero.meters["powder"] = 0.0
    prize.meters["dirty"] = 0.0
    world.say(f"{hero.id} used {GEAR[1].label}, wiped the shelf clean, and put the tin away with a careful tap.")
    world.say(f"At the end, {hero.id} chose to be gentle with the creme powder, and the room stayed neat and bright.")

    world.facts.update(hero=hero, keeper=keeper, action=action, prize=prize, setting=setting)
    return world


def explain_rejection(action: Action, prize: Prize) -> str:
    return f"(No story: {action.gerund} and {prize.label} don't make a reasonable cautionary conflict here.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "action", None) and getattr(args, "prize", None):
        if getattr(args, "action", None) not in ACTIONS or getattr(args, "prize", None) not in PRIZES:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    return StoryParams(place=place, action=action, prize=prize, name=getattr(args, "name", None) or rng.choice(["Wally", "Milo", "Juno", "Pip"]))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary tall tale storyworld about a wallaby and creme powder.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
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


ASP_RULES = r"""
valid(Place, Action, Prize) :- affords(Place, Action), prize(Prize), action(Action).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", p, a))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [StoryParams(place="pantry", action="shake", prize="tin", name="Wally")]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
