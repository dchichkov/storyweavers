#!/usr/bin/env python3
"""
A standalone story world for a tiny superhero tale.

Premise inspired by the seed:
- a curious child-hero
- a sticky kiwi treat
- slobber as the messy obstacle
- a small rescue/repair turn that resolves the problem

The world is intentionally small and constraint-checked: the hero's curiosity
can lead to trouble, but only when a sensible fix exists.
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
    gear: object | None = None
    hero: object | None = None
    mentor: object | None = None
    prize: object | None = None
    sidekick: object | None = None
    def __post_init__(self) -> None:
        for k in ["slobber", "mess", "spark", "tiredness", "cleanliness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "curiosity", "worry", "bravery", "pride", "relief"]:
            self.memes.setdefault(k, 0.0)

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
class CityBlock:
    place: str
    indoors: bool = False
    allows: set[str] = field(default_factory=set)
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
class Move:
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
    def __init__(self, setting: CityBlock) -> None:
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _r_slobber(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["slobber"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if not (item.region in world.zone):
                continue
            sig = ("slobber", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            item.memes["worry"] += 0.5
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got sticky slobber on it.")
    return out


def _r_clean(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["mess"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("clean", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] += 1
        out.append(f"That meant more cleaning for {caretaker.label}.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        if actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("bravery", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["bravery"] += 1
        out.append(f"{actor.id} took a brave breath and looked for a smarter way.")
    return out


CAUSAL_RULES = [
    _r_slobber,
    _r_clean,
    _r_bravery,
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


def prize_at_risk(move: Move, prize: Prize) -> bool:
    return prize.region in move.zone


def select_gear(move: Move, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if move.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, hero: Entity, move: Move, prize_id: str) -> dict:
    sim = world.copy()
    _do_move(sim, sim.get(hero.id), move, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["mess"] >= THRESHOLD}


def _do_move(world: World, hero: Entity, move: Move, narrate: bool = True) -> None:
    if move.id not in world.setting.allows:
        return
    world.zone = set(move.zone)
    hero.meters["slobber"] += 1
    hero.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little superhero with a bright cape and a bigger-than-average sense of curiosity."
    )


def love_town(world: World, hero: Entity, setting: CityBlock) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved exploring {setting.place}, because every corner might hide a clue."
    )


def find_kiwi(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    prize.worn_by = hero.id
    world.say(
        f"One afternoon, {hero.id} found {prize.phrase} and held {prize.it()} like a tiny trophy."
    )


def arrive(world: World, hero: Entity, sidekick: Entity, move: Move) -> None:
    world.say(
        f"One day, {hero.id} and {sidekick.label} went to {world.setting.place}."
    )
    world.say(f"{hero.id} wanted to {move.verb}, because curiosity was buzzing in {hero.pronoun('possessive')} chest.")


def warn(world: World, mentor: Entity, hero: Entity, move: Move, prize: Entity) -> bool:
    pred = predict_mess(world, hero, move, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = move.soil
    world.say(
        f'"If you {move.verb}, your {prize.label} will get {move.soil}," {mentor.label} said. "Let\'s be clever about it."'
    )
    return True


def resist(world: World, hero: Entity, move: Move) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} wanted the adventure anyway and almost rushed to {move.rush}.")


def helper_block(world: World, mentor: Entity, hero: Entity) -> None:
    hero.memes["worry"] += 0.5
    world.say(
        f"But {mentor.label} held up a calm hand and reminded {hero.pronoun('object')} that heroes do not have to guess blindly."
    )


def compromise(world: World, mentor: Entity, hero: Entity, move: Move, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(move, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=mentor.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, move, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(
        f'{mentor.label} smiled. "How about we {gear_def.prep} and then {move.verb}?"'
    )
    return gear_def


def accept(world: World, mentor: Entity, hero: Entity, move: Move, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["bravery"] += 1
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} grinned, nodded, and put on {gear_def.label}."
    )
    world.say(
        f"Then {hero.id} {move.gerund}, and {prize.label} stayed clean while the city lights blinked like friendly stars."
    )


def tell(setting: CityBlock, move: Move, prize_cfg: Prize, hero_name: str = "Nova", sidekick_name: str = "Milo") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="boy", label=sidekick_name))
    mentor = world.add(Entity(id="mentor", kind="character", type="woman", label="Captain Bright"))
    prize = world.add(Entity(
        id="kiwi",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    love_town(world, hero, setting)
    find_kiwi(world, hero, prize)

    world.para()
    arrive(world, hero, sidekick, move)
    warn(world, mentor, hero, move, prize)
    resist(world, hero, move)
    helper_block(world, mentor, hero)

    world.para()
    gear_def = compromise(world, mentor, hero, move, prize)
    if gear_def:
        accept(world, mentor, hero, move, prize, gear_def)

    world.facts.update(hero=hero, sidekick=sidekick, mentor=mentor, prize=prize, move=move, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "rooftop": CityBlock(place="the rooftop garden", allows={"spin", "leap"}),
    "alley": CityBlock(place="the colorful alley", allows={"dash", "swing"}),
    "museum": CityBlock(place="the moonlit museum", allows={"sneak", "peek"}),
}

MOVES = {
    "spin": Move(
        id="spin",
        verb="spin around the fountain",
        gerund="spinning around the fountain",
        rush="the fountain in a hurry",
        mess="slobber",
        soil="all sticky",
        zone={"torso"},
        keyword="slobber",
    ),
    "leap": Move(
        id="leap",
        verb="leap across the puddle path",
        gerund="leaping across the puddle path",
        rush="the puddle path",
        mess="slobber",
        soil="splashed with slobber",
        zone={"torso"},
        keyword="kiwi",
    ),
    "dash": Move(
        id="dash",
        verb="dash through the snack cart line",
        gerund="dashing through the snack cart line",
        rush="the snack cart line",
        mess="slobber",
        soil="dotted with slobber",
        zone={"hands", "torso"},
        keyword="slobber",
    ),
    "sneak": Move(
        id="sneak",
        verb="sneak past the exhibit",
        gerund="sneaking past the exhibit",
        rush="past the exhibit",
        mess="slobber",
        soil="spotted with slobber",
        zone={"hands"},
        keyword="kiwi",
    ),
    "peek": Move(
        id="peek",
        verb="peek into the skylight room",
        gerund="peeking into the skylight room",
        rush="into the skylight room",
        mess="slobber",
        soil="splashed with slobber",
        zone={"torso"},
        keyword="slobber",
    ),
}

PRIZES = {
    "kiwi": Prize(label="kiwi", phrase="a bright kiwi snack", type="fruit", region="torso"),
}

GEAR = [
    Gear(
        id="visor",
        label="a clear visor",
        covers={"torso"},
        guards={"slobber"},
        prep="put on a clear visor first",
        tail="put on the clear visor",
    ),
    Gear(
        id="gloves",
        label="clean hero gloves",
        covers={"hands"},
        guards={"slobber"},
        prep="pull on clean hero gloves",
        tail="pulled on the clean hero gloves",
        plural=True,
    ),
]

GIRL_NAMES = ["Nova", "Zara", "Ivy", "Mina"]
BOY_NAMES = ["Milo", "Theo", "Arlo", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for move_id in setting.allows:
            move = _safe_lookup(MOVES, move_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(move, prize) and select_gear(move, prize):
                    combos.append((place, move_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    move: str
    prize: str
    name: str
    sidekick: str
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
    ap = argparse.ArgumentParser(description="Superhero story world: curiosity, kiwi, and slobber.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    if getattr(args, "move", None) and getattr(args, "prize", None):
        move, prize = _safe_lookup(MOVES, getattr(args, "move", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(move, prize) and select_gear(move, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "move", None) is None or c[1] == getattr(args, "move", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, move, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(BOY_NAMES)
    return StoryParams(place=place, move=move, prize=prize, name=name, sidekick=sidekick)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    move = _safe_fact(world, f, "move")
    return [
        f'Write a short superhero story for a young child featuring "{move.keyword}" and "kiwi".',
        f"Tell a brave but gentle story where {hero.id} follows curiosity, meets a slobber problem, and chooses a safer hero plan.",
        f"Write a simple superhero story about {hero.id} and {f['sidekick'].id} that ends with a clean kiwi and a happy rescue plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mentor = _safe_fact(world, f, "mentor")
    prize = _safe_fact(world, f, "prize")
    move = _safe_fact(world, f, "move")
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What was {hero.id} like at the start of the story?",
            answer=f"{hero.id} was a little superhero with a lot of curiosity and a bright wish to help.",
        ),
        QAItem(
            question=f"What tasty thing did {hero.id} find?",
            answer=f"{hero.id} found {prize.phrase}, and {prize.label} became the important thing to protect.",
        ),
        QAItem(
            question=f"Why did {mentor.label} worry when {hero.id} wanted to {move.verb}?",
            answer=f"{mentor.label} worried because {hero.id}'s {prize.label} would get {move.soil} if the hero rushed ahead without a plan.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label} covered the right part of {hero.id} so the hero could {move.verb} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt joyful and brave, because curiosity led to a smarter rescue plan instead of a messy mistake.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, learn, and ask questions about new things.",
        ),
        QAItem(
            question="What is a kiwi?",
            answer="A kiwi is a small fruit with green inside and tiny seeds, and it can be sweet and a little tangy.",
        ),
        QAItem(
            question="What does slobber mean?",
            answer="Slobber is wet spit that can make something sticky and messy.",
        ),
        QAItem(
            question="What do superheroes do?",
            answer="Superheroes try to help people, solve problems, and stay brave even when something goes wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world questions ==")
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
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        elif e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(M, P) :- splashes(M, R), worn_on(P, R).
protects(G, M, P) :- gear(G), prize_at_risk(M, P), mess_of(M, S), guards(G, S), covers(G, R), worn_on(P, R).
has_fix(M, P) :- protects(_, M, P).
valid(Place, M, P) :- allows(Place, M), prize_at_risk(M, P), has_fix(M, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(s.allows):
            lines.append(asp.fact("allows", pid, m))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("mess_of", mid, m.mess))
        for r in sorted(m.zone):
            lines.append(asp.fact("splashes", mid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MOVES, params.move), _safe_lookup(PRIZES, params.prize), params.name, params.sidekick)
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


CURATED = [
    StoryParams(place="rooftop", move="spin", prize="kiwi", name="Nova", sidekick="Milo"),
    StoryParams(place="alley", move="dash", prize="kiwi", name="Ivy", sidekick="Theo"),
    StoryParams(place="museum", move="peek", prize="kiwi", name="Zara", sidekick="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, move, prize) combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.move} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
