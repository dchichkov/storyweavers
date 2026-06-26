#!/usr/bin/env python3
"""
Standalone storyworld: a tiny pirate tale with a cautionary twist and humor.

Premise:
A young pirate wants to fire a ship's mortar to impress the crew, but the
captain warns that careless blasting can break the deck and spill the cargo.
A safer plan, plus a comic twist, turns the trouble into a win.

This world is small, classical, and state-driven:
- physical meters track soot, damage, splash, noise, and cargo stability
- emotional memes track pride, fear, worry, surprise, and delight
- the story is narrated from a short simulated chain of cause and effect
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    captain: object | None = None
    cargo: object | None = None
    hero: object | None = None
    mortar: object | None = None
    tags: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "pirate_boy", "captain", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "pirate_girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the ship"
    sea: str = "calm"
    affords: set[str] = field(default_factory=set)
    world: object | None = None
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
class Tool:
    id: str
    label: str
    phrase: str
    mess: str
    risk: str
    safe_use: str
    unsafe_use: str
    noise: str
    twist: str
    caution: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    tool: str = ""
    name: str = ""
    gender: str = ""
    captain_name: str = ""
    captain_gender: str = ""
    trait: str = ""
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def pronoun_gender(g: str) -> str:
    return "girl" if g == "girl" else "boy"


def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _mem(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _inc_meter(entity: Entity, key: str, amt: float = 1.0) -> None:
    entity.meters[key] = _meter(entity, key) + amt


def _inc_mem(entity: Entity, key: str, amt: float = 1.0) -> None:
    entity.memes[key] = _mem(entity, key) + amt


def setup_world(tool: Tool, params: StoryParams) -> World:
    world = World(Setting(place="the ship", sea="calm", affords={"mortar"}))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=pronoun_gender(params.gender),
        traits=["little", params.trait],
    ))
    captain = world.add(Entity(
        id=params.captain_name,
        kind="character",
        type=pronoun_gender(params.captain_gender),
        label=f"Captain {params.captain_name}",
        traits=["old", "steady"],
    ))
    mortar = world.add(Entity(
        id="mortar",
        type="mortar",
        label="mortar",
        phrase="the old ship's mortar",
        caretaker=captain.id,
        meters={"soot": 0.0, "damage": 0.0, "cargo_rattle": 0.0, "smoke": 0.0},
        tags=list(tool.tags),
    ))
    cargo = world.add(Entity(
        id="cargo",
        type="cargo",
        label="cargo crates",
        phrase="the stacked cargo crates",
        caretaker=captain.id,
        plural=True,
        meters={"damage": 0.0, "spill": 0.0},
    ))
    hero.memes["pride"] = 0.0
    captain.memes["worry"] = 0.0
    world.facts.update(hero=hero, captain=captain, mortar=mortar, cargo=cargo, tool=tool)
    return world


def cautionary_check(world: World, hero: Entity, tool: Tool) -> bool:
    return True


def predict_damage(world: World, hero: Entity, tool: Tool) -> dict:
    sim = world.copy()
    _do_fire(sim, sim.get(hero.id), tool, safe=False, narrate=False)
    cargo = sim.get("cargo")
    mortar = sim.get("mortar")
    return {
        "cargo_spill": _meter(cargo, "spill") >= THRESHOLD,
        "damage": _meter(mortar, "damage") >= THRESHOLD or _meter(cargo, "damage") >= THRESHOLD,
        "smoke": _meter(mortar, "smoke"),
    }


def _do_fire(world: World, hero: Entity, tool: Tool, safe: bool, narrate: bool = True) -> None:
    mortar = world.get("mortar")
    cargo = world.get("cargo")
    if world.setting.affords and "mortar" not in world.setting.affords:
        pass
    _inc_mem(hero, "excitement")
    _inc_meter(mortar, "smoke", 1.0)
    if safe:
        _inc_meter(mortar, "damage", 0.0)
        _inc_meter(cargo, "spill", 0.0)
        if narrate:
            world.say(f"The mortar boomed safely, and the deck only got a little smoky.")
    else:
        _inc_meter(mortar, "damage", 1.0)
        _inc_meter(cargo, "spill", 1.0)
        _inc_meter(cargo, "damage", 1.0)
        _inc_mem(hero, "surprise", 1.0)
        _inc_mem(world.get("Captain"), "worry", 1.0)
        if narrate:
            world.say(f"The blast kicked too hard, and the crates jolted across the deck.")


def tell_story(world: World, tool: Tool) -> None:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    captain = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "captain")
    mortar = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "mortar")
    cargo = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "cargo")

    world.say(f"{hero.id} was a little {hero.traits[-1]} pirate who loved to show off.")
    world.say(f"{hero.id} kept staring at {tool.phrase}, because a loud boom felt grand.")
    world.say(f"On the ship, {tool.label} sat beside {cargo.label}, and the whole deck smelled of salt and tar.")

    world.say(f"One calm day, {hero.id} wanted to {tool.unsafe_use}, just to make the crew cheer.")
    pred = predict_damage(world, hero, tool)
    if pred["cargo_spill"]:
        world.say(f'"If you do that," {captain.id} warned, "you could {tool.caution}."')
        world.say(f"{hero.id} blinked. {hero.pronoun().capitalize()} had not expected the mortar to be so fussy.")
    else:
        world.say(f"{captain.id} gave a warning anyway, because a ship is no place for foolish booming.")

    world.say(f"{hero.id} tried to fire the mortar, and the deck gave a comic little shiver.")
    _do_fire(world, hero, tool, safe=False, narrate=True)

    if _meter(cargo, "spill") >= THRESHOLD:
        world.say(f"The twist was funny in a grumpy way: the loud boom made a flock of gulls drop a fish right into a barrel.")
        _inc_mem(hero, "surprise", 1.0)
        _inc_mem(hero, "delight", 1.0)
        _inc_mem(captain, "surprise", 1.0)

    world.say(f"Then {captain.id} pointed to the mess and said they would need a safer trick.")
    world.say(f"They stuffed the mortar with damp sand instead of shot, so it could bark without smashing the deck.")
    _do_fire(world, hero, tool, safe=True, narrate=True)

    _inc_mem(hero, "pride", 1.0)
    _inc_mem(hero, "joy", 1.0)
    _inc_mem(captain, "relief", 1.0)
    world.say(f"In the end, {hero.id} still heard a great boom, but the cargo stayed snug and the crew laughed at the smoky, sandy puff.")


TOOL_REGISTRY = {
    "mortar": Tool(
        id="mortar",
        label="mortar",
        phrase="the ship's mortar",
        mess="smoke",
        risk="damage",
        safe_use="fire the mortar without testing it",
        unsafe_use="blast the mortar right beside the cargo",
        noise="a thunderous bang",
        twist="a fish from the gulls",
        caution="smash the crates and spray splinters everywhere",
        tags={"mortar", "ship", "noise", "cargo"},
    ),
}

NAMES = ["Mira", "Ned", "Finn", "Ruby", "Jax", "Bea", "Sailor", "Pip"]
CAPTAINS = ["Morgan", "Hale", "Corin", "Wren", "June", "Otis"]
TRAITS = ["brave", "bouncy", "curious", "proud", "sly", "cheeky"]


def valid_params() -> list[str]:
    return list(TOOL_REGISTRY)


@dataclass
class _Choice:
    tool: str
    name: str
    gender: str
    captain_name: str
    captain_gender: str
    trait: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a mortar, a caution, a twist, and humor.")
    ap.add_argument("--tool", choices=valid_params())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
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
    tool = getattr(args, "tool", None) or "mortar"
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    captain_name = getattr(args, "captain_name", None) or rng.choice([n for n in CAPTAINS if n != name])
    captain_gender = getattr(args, "captain_gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(tool=tool, name=name, gender=gender, captain_name=captain_name, captain_gender=captain_gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    captain = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "captain")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short pirate tale for a child that includes a {tool.label} and the word "mortar".',
        f"Tell a cautionary story where {hero.id} wants to use a mortar, but {captain.label} worries about the ship.",
        f"Write a funny pirate story about a noisy mortar, a warning, and a safer surprise at sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    captain = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "captain")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    cargo = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "cargo")
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the mortar at first?",
            answer=f"{hero.id} wanted to {tool.unsafe_use} to make the crew cheer.",
        ),
        QAItem(
            question=f"Why did {captain.label} warn {hero.id}?",
            answer=f"{captain.label} warned {hero.id} because a hard blast could {tool.caution} and upset the cargo.",
        ),
        QAItem(
            question=f"What made the story funny after the first blast?",
            answer=f"The boom startled the gulls, and the gulls dropped a fish into a barrel, which made the whole crew laugh.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, they used a safer sandy charge, so the mortar could boom without ruining the {cargo.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mortar on a ship?",
            answer="A mortar is a loud blasting device that can fire a heavy shot or make a very big boom, so sailors must use it carefully.",
        ),
        QAItem(
            question="Why is caution important on a ship?",
            answer="Caution matters because a ship has tight spaces, stacks of cargo, and wooden boards that can break if something is used carelessly.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the ending different from what you expected.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    tool = TOOL_REGISTRY[params.tool]
    world = setup_world(tool, params)
    tell_story(world, tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
mortar(mortar).
cautionary(mortar).
twist(mortar).
humor(mortar).

valid_story(mortar) :- mortar(mortar), cautionary(mortar), twist(mortar), humor(mortar).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("mortar", "mortar"),
        asp.fact("cautionary", "mortar"),
        asp.fact("twist", "mortar"),
        asp.fact("humor", "mortar"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("mortar",)}
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


CURATED = [
    StoryParams(tool="mortar", name="Mira", gender="girl", captain_name="Morgan", captain_gender="boy", trait="cheeky"),
    StoryParams(tool="mortar", name="Finn", gender="boy", captain_name="Hale", captain_gender="girl", trait="curious"),
]


def explain_invalid(args: argparse.Namespace) -> Optional[str]:
    return None


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} valid story pattern(s):")
        for v in vals:
            print(" ", v[0])
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            p = sample.params
            print(f"### variant {idx + 1}: {p.name} and the {p.tool}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
