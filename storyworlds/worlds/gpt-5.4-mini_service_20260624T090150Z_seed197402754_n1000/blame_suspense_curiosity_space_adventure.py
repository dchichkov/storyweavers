#!/usr/bin/env python3
"""
A small storyworld about a space adventure with blame, suspense, and curiosity.

A curious child crew member spots a strange problem on a ship, someone gets
blamed too quickly, and the story resolves with a careful check that reveals
what really happened.
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
    location: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    leader: object | None = None
    module_ent: object | None = None
    suspicious: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "captain", "pilot"}
        male = {"boy", "man", "engineer", "mechanic"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
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
class Ship:
    name: str
    place: str
    modules: list[str]
    alert: str = "green"
    clues: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
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
class StoryParams:
    ship: str
    module: str
    culprit: str
    hero: str
    hero_type: str
    leader: str
    leader_type: str
    mystery: str
    seed: Optional[int] = None
    params: object | None = None
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
class ModuleSpec:
    id: str
    label: str
    clue: str
    real_cause: str
    blame_target: str
    suspense_line: str
    curiosity_line: str
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


@dataclass
class CulpritSpec:
    id: str
    label: str
    kind: str
    hint: str
    harmless: bool = True
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


SHIP_REGISTRY = {
    "comet_star": Ship(
        name="the Comet Star",
        place="deep space",
        modules=["engine", "radar", "cargo bay", "observation dome"],
    ),
    "moon_whisper": Ship(
        name="the Moon Whisper",
        place="orbit around a blue moon",
        modules=["engine", "radar", "cargo bay", "map room"],
    ),
    "sun_sprinter": Ship(
        name="the Sun Sprinter",
        place="the edge of a warm asteroid belt",
        modules=["engine", "radar", "cargo bay", "lounge"],
    ),
}

MODULES = {
    "engine": ModuleSpec(
        id="engine",
        label="engine room",
        clue="a loose silver bolt under the panel",
        real_cause="a tiny bolt had slipped out and rattled under the panel",
        blame_target="the helper drone",
        suspense_line="The engine thumped once, then went quiet again.",
        curiosity_line="Mira wanted to know why the light kept blinking even when the engine looked fine.",
    ),
    "radar": ModuleSpec(
        id="radar",
        label="radar screen",
        clue="a dust speck on the glass",
        real_cause="a floating dust speck had made the radar look like it saw a dot moving by itself",
        blame_target="the navigation chart",
        suspense_line="A small dot blinked on the radar, then vanished.",
        curiosity_line="Theo leaned closer, wondering whether the dot was a ship, a moon chip, or just dust.",
    ),
    "cargo bay": ModuleSpec(
        id="cargo",
        label="cargo bay",
        clue="a snapped strap on a crate",
        real_cause="a crate strap had snapped when the ship turned too fast",
        blame_target="the supply crate",
        suspense_line="Something in the cargo bay gave a soft bang in the dark.",
        curiosity_line="Nia wanted to peek at the crate and see what was hiding inside the shadows.",
    ),
    "observation dome": ModuleSpec(
        id="dome",
        label="observation dome",
        clue="a tiny crack in the glass sticker",
        real_cause="a sticker edge had curled up and made the dome sensor blink",
        blame_target="the star map",
        suspense_line="The dome lights flickered like a secret was passing overhead.",
        curiosity_line="Jules stared at the dome and wondered why the stars looked almost like they were whispering.",
    ),
    "map room": ModuleSpec(
        id="map",
        label="map room",
        clue="a marker rolling under the table",
        real_cause="a marker had rolled under the table and bumped the map reader",
        blame_target="the captain's notes",
        suspense_line="The map room made a strange clicking sound in the quiet.",
        curiosity_line="Ari kept asking what the clicking meant and whether the ship was trying to tell them something.",
    ),
    "lounge": ModuleSpec(
        id="lounge",
        label="lounge",
        clue="a sticky cup lid near the console",
        real_cause="a cup lid had stuck to the console and blocked one button",
        blame_target="the snack drawer",
        suspense_line="The lounge console blinked twice, then held its breath.",
        curiosity_line="Pip wondered why the button felt stiff and what had hidden beneath the lid.",
    ),
}

CULPRITS = {
    "drone": CulpritSpec(
        id="drone",
        label="helper drone",
        kind="robot",
        hint="The drone had rolled by earlier, but it was only carrying towels.",
    ),
    "crate": CulpritSpec(
        id="crate",
        label="supply crate",
        kind="object",
        hint="The crate looked heavy, but nothing had broken inside it.",
    ),
    "map": CulpritSpec(
        id="map",
        label="navigation chart",
        kind="object",
        hint="The chart had a bent corner, but it was not causing the trouble.",
    ),
    "stars": CulpritSpec(
        id="stars",
        label="star window",
        kind="object",
        hint="The star window was bright, but the problem was not out in space.",
    ),
    "snacks": CulpritSpec(
        id="snacks",
        label="snack drawer",
        kind="object",
        hint="The snack drawer was messy, but it was not the real culprit.",
    ),
}

HEROES = ["Mira", "Theo", "Nia", "Jules", "Ari", "Pip"]
LEADERS = ["Captain Sol", "Commander Nova", "Pilot Ray", "Captain Luma"]
HERO_TYPES = ["girl", "boy"]
LEADER_TYPES = ["captain", "pilot"]
MYSTERIES = ["blink", "rattle", "click", "flicker", "thump"]


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with blame and curiosity.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--module", choices=MODULES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--leader")
    ap.add_argument("--leader-type", choices=LEADER_TYPES)
    ap.add_argument("--mystery", choices=MYSTERIES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for ship in SHIP_REGISTRY:
        for module in MODULES:
            for culprit in CULPRITS:
                combos.append((ship, module, culprit))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "ship", None):
        combos = [c for c in combos if c[0] == getattr(args, "ship", None)]
    if getattr(args, "module", None):
        combos = [c for c in combos if c[1] == getattr(args, "module", None)]
    if getattr(args, "culprit", None):
        combos = [c for c in combos if c[2] == getattr(args, "culprit", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    ship, module, culprit = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    leader_type = getattr(args, "leader_type", None) or rng.choice(LEADER_TYPES)
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    leader = getattr(args, "leader", None) or rng.choice(LEADERS)
    mystery = getattr(args, "mystery", None) or rng.choice(MYSTERIES)
    return StoryParams(ship, module, culprit, hero, hero_type, leader, leader_type, mystery)


def tell(params: StoryParams) -> World:
    ship = SHIP_REGISTRY[params.ship]
    module = _safe_lookup(MODULES, params.module)
    culprit = _safe_lookup(CULPRITS, params.culprit)
    world = World(ship)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    leader = world.add(Entity(id=params.leader, kind="character", type=params.leader_type, label=params.leader))
    suspicious = world.add(Entity(id=culprit.id, kind="thing", type=culprit.kind, label=culprit.label))
    module_ent = world.add(Entity(id=module.id, kind="thing", type="module", label=module.label))

    hero.memes["curiosity"] = 1
    hero.memes["suspense"] = 1

    world.say(f"On {ship.name}, {hero.id} was the first one to notice something odd in the {module.label}.")
    world.say(f"{module.suspense_line} {hero.id} stared at the blinking light and felt a prickly kind of suspense.")
    world.say(f"{hero.id} had a big question: why did the {params.mystery} sound come from there?")
    world.say(f"{module.curiosity_line}")

    world.para()
    world.say(f"{leader.id} hurried in and saw the problem. At once, {leader.pronoun('subject')} blamed the {culprit.label}.")
    world.say(f'"It must be the {culprit.label}," {leader.pronoun("subject")} said, even before looking twice.')
    world.say(f"But {hero.id} noticed a clue: {module.clue}.")

    world.para()
    world.say(f"{hero.id} stayed calm and checked the floor, the panel, and the corners one by one.")
    world.say(f"That careful search showed the truth: {module.real_cause}.")
    world.say(f"{culprit.hint}")
    world.say(f"{leader.id} blinked, then laughed softly. The blame was wrong, and the mystery was solved.")

    world.para()
    world.say(f"After the fix, the ship hummed steady again. {hero.id} felt proud for asking questions instead of guessing.")
    world.say(f"{leader.id} thanked {hero.id} for the curiosity that saved the day, and the crew sailed on through the stars.")

    world.facts.update(
        hero=hero,
        leader=leader,
        culprit=suspicious,
        module=module_ent,
        module_spec=module,
        culprit_spec=culprit,
        ship=ship,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    leader = _safe_fact(world, f, "leader")
    module = _safe_fact(world, f, "module_spec")
    culprit = _safe_fact(world, f, "culprit_spec")
    return [
        f'Write a short space adventure for young children that includes the word "blame".',
        f"Tell a story where {hero.id} feels curiosity about a strange problem in the {module.label}, "
        f"but {leader.id} blames the {culprit.label} too fast.",
        f"Write a gentle suspense story on {f['ship'].name} where careful looking shows the real cause of the trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    leader = _safe_fact(world, f, "leader")
    module = _safe_fact(world, f, "module_spec")
    culprit = _safe_fact(world, f, "culprit_spec")
    return [
        QAItem(
            question=f"Who noticed the strange problem first on {f['ship'].name}?",
            answer=f"{hero.id} noticed it first in the {module.label}. {hero.id} was curious and looked closely instead of guessing.",
        ),
        QAItem(
            question=f"Why did {leader.id} blame the {culprit.label} at first?",
            answer=f"{leader.id} saw the trouble and blamed the {culprit.label} too quickly, before checking the clue in the {module.label}.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery in the {module.label}?",
            answer=f"The clue was {module.clue}. That clue helped {hero.id} notice what was really wrong.",
        ),
        QAItem(
            question=f"What really caused the problem in the {module.label}?",
            answer=f"The real cause was that {module.real_cause}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the mystery was solved?",
            answer=f"{hero.id} felt proud because curiosity helped fix the problem and the ship was safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to ask questions and learn how something works.",
        ),
        QAItem(
            question="What does blame mean?",
            answer="Blame means saying someone or something caused a problem, sometimes before you know for sure.",
        ),
        QAItem(
            question="Why should a person check clues before blaming someone?",
            answer="Checking clues first helps people find the real cause instead of making a wrong guess.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} kind={e.kind} label={e.label}")
    return "\n".join(lines)


ASP_RULES = r"""
ship(S) :- ship_fact(S).
module(M) :- module_fact(M).
culprit(C) :- culprit_fact(C).
valid_combo(S,M,C) :- ship(S), module(M), culprit(C).
"""


def asp_facts() -> str:
    import asp
    out = []
    for s in SHIP_REGISTRY:
        out.append(asp.fact("ship_fact", s))
    for m in MODULES:
        out.append(asp.fact("module_fact", m))
    for c in CULPRITS:
        out.append(asp.fact("culprit_fact", c))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "asp", None):
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for ship, module, culprit in valid_combos():
            params = StoryParams(
                ship=ship,
                module=module,
                culprit=culprit,
                hero=random.choice(HEROES),
                hero_type=random.choice(HERO_TYPES),
                leader=random.choice(LEADERS),
                leader_type=random.choice(LEADER_TYPES),
                mystery=random.choice(MYSTERIES),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
            header = f"### {p.hero} aboard {p.ship} in {p.module} (culprit: {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
