#!/usr/bin/env python3
"""
A tiny pirate-tale story world about a chowmein caper, a lesson learned, and
a bad ending told with a rhyme.

The seed idea:
- A pirate crew is on a small ship.
- A hungry pirate notices a hot bowl of chowmein.
- Someone warns them to wait.
- The pirate rushes anyway, the bowl spills, and the meal is lost.
- The ending is "bad" in the sense that nobody gets the chowmein, but the
  pirate learns to ask first and to mind the deck.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports shared results eagerly
- lazy ASP import
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: str = ""
    captain: object | None = None
    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pirate", "boy", "man", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
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
    place: str = "the little ship"
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
    keyword: str = ""
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class Rule:
    name: str
    apply: callable
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


def _apply_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("clumsy", 0.0) < THRESHOLD and actor.meters.get("rush", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("hot_chowmein", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != actor.id or item.worn_by != actor.id:
                continue
            if item.region not in world.zone:
                continue
            sig = ("spill", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
            item.meters["saucy"] = item.meters.get("saucy", 0.0) + 1.0
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got saucy and dirty.")
    return out


def _apply_empty_belly(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("hunger", 0.0) < THRESHOLD:
            continue
        sig = ("hunger", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["grumpy"] = actor.memes.get("grumpy", 0.0) + 1.0
        out.append(f"{actor.id}'s belly rumbled louder than the gulls.")
    return out


CAUSAL_RULES = [
    Rule("spill", _apply_spill),
    Rule("empty_belly", _apply_empty_belly),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        pass
    world.zone = set(action.zone)
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1.0
    actor.meters["hot_chowmein"] = actor.meters.get("hot_chowmein", 0.0) + 1.0
    actor.meters["rush"] = actor.meters.get("rush", 0.0) + 1.0
    propagate(world, narrate=narrate)


def predict_spill(world: World, actor: Entity, action: Action, prize_id: str) -> bool:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.fired = set(world.fired)
    sim.zone = set(world.zone)
    sim.facts = dict(world.facts)
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("dirty", 0.0) >= THRESHOLD


def chorus(word: str, line: str) -> str:
    return f"{line} — {word}, chowmein, on the brine."


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"On a little ship with a swaying mast, {hero.id} was a {', '.join(hero.traits)} pirate who loved a full belly."
    )


def craving(world: World, hero: Entity, action: Action) -> None:
    hero.meters["hunger"] = hero.meters.get("hunger", 0.0) + 1.0
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    world.say(
        f"{hero.pronoun().capitalize()} sniffed the air and grinned, because the galley smelled like {action.keyword}."
    )


def set_out(world: World, hero: Entity, action: Action, prize: Entity) -> None:
    world.say(
        f"Near the rail, a warm bowl of {prize.phrase} waited, and {hero.id} wanted to {action.verb} right away."
    )


def warn(world: World, captain: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    if not predict_spill(world, hero, action, prize.id):
        return False
    world.say(
        f"\"Wait, matey,\" said {captain.id}. \"If you rush now, that {prize.label} will spill on the deck.\""
    )
    return True


def ignore_warning(world: World, hero: Entity, action: Action) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1.0
    world.say(f"But {hero.id} had a hungry blink and tried to {action.rush}.")


def slip_and_spill(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["oops"] = hero.memes.get("oops", 0.0) + 1.0
    world.say(
        f"{hero.id} slipped on the wet plank, and the bowl tipped over in a brown-and-golden splash."
    )
    world.say(
        f"The chowmein slid under a barrel, and the gulls pecked at the noodles before anyone could catch them."
    )


def lesson(world: World, captain: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1.0
    world.say(
        f"{hero.id} hung {hero.pronoun('possessive')} head and listened when {captain.id} said,"
        f" \"A fast bite can make a sad sight; ask first, and keep your feet light.\""
    )
    world.say(
        f"So the crew ate plain ship biscuit instead, and {hero.id} learned to wait for the next pot of {prize.label}."
    )


SETTINGS = {
    "ship": Setting(place="the little ship", affords={"chowmein"}),
}

ACTIONS = {
    "chowmein": Action(
        id="chowmein",
        verb="eat the chowmein",
        gerund="eating chowmein",
        rush="dash to the galley",
        mess="sticky",
        soil="spilled",
        zone={"deck"},
        keyword="chowmein",
        tags={"food", "noodles", "mess"},
    ),
}

PRIZES = {
    "chowmein": Prize(
        label="chowmein",
        phrase="a steaming bowl of chowmein",
        type="bowl",
        region="deck",
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Tess"]
BOY_NAMES = ["Bram", "Jory", "Finn"]
PIRATE_TRAITS = ["brisk", "greedy", "cheeky", "sunburnt"]


@dataclass
class StoryParams:
    setting: str
    action: str
    prize: str
    name: str
    role: str
    captain: str
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


def build_story(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="pirate" if params.role == "pirate" else params.role,
        traits=["little", params.trait, "pirate"],
    ))
    captain = world.add(Entity(
        id=params.captain,
        kind="character",
        type="captain",
        traits=["old", "steady", "captain"],
    ))
    prize = world.add(Entity(
        id="bowl",
        type="bowl",
        label="bowl",
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        owner=hero.id,
        caretaker=captain.id,
        region="deck",
    ))
    prize.worn_by = hero.id

    introduce(world, hero)
    craving(world, hero, _safe_lookup(ACTIONS, params.action))
    set_out(world, hero, _safe_lookup(ACTIONS, params.action), prize)

    world.para()
    warned = warn(world, captain, hero, _safe_lookup(ACTIONS, params.action), prize)
    if warned:
        ignore_warning(world, hero, _safe_lookup(ACTIONS, params.action))
    _do_action(world, hero, _safe_lookup(ACTIONS, params.action), narrate=True)
    slip_and_spill(world, hero, prize)

    world.para()
    lesson(world, captain, hero, prize)
    world.say(chorus("Yo-ho", "The ship sailed on with an empty bowl and a wiser deck"))
    world.facts.update(hero=hero, captain=captain, prize=prize, action=_safe_lookup(ACTIONS, params.action), warned=warned)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "action")
    return [
        f'Write a short pirate tale that includes the word "{act.keyword}" and ends with a rhyme.',
        f"Tell a story where a pirate named {hero.id} wants to {act.verb} but learns a lesson the hard way.",
        f"Make a child-friendly bad-ending ship tale about {act.keyword}, a spill, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    captain: Entity = _safe_fact(world, f, "captain")
    prize: Entity = _safe_fact(world, f, "prize")
    act: Action = _safe_fact(world, f, "action")
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} on the ship?",
            answer=f"{hero.id} the pirate wanted to {act.verb} on the little ship.",
        ),
        QAItem(
            question=f"What did {captain.id} warn would happen if {hero.id} rushed?",
            answer=f"{captain.id} warned that the chowmein would spill on the deck if {hero.id} rushed.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} at the end?",
            answer="The bowl tipped over, the chowmein spilled, and the gulls pecked at the noodles.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer="The pirate learned to ask first and to keep a careful step on a slippery deck.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "food": [
        QAItem(
            question="What is chowmein?",
            answer="Chowmein is a noodle dish that is often cooked with vegetables and sauce.",
        )
    ],
    "noodles": [
        QAItem(
            question="What are noodles?",
            answer="Noodles are long, thin strips of dough that people cook and eat in many meals.",
        )
    ],
    "mess": [
        QAItem(
            question="Why is a spilled bowl messy?",
            answer="A spilled bowl makes a mess because food can slide, splash, and stick where it should not be.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    out: list[QAItem] = []
    for tag in ["food", "noodles", "mess"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this pirate world only supports chowmein on the ship.)"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("ship", "chowmein", "chowmein")]


CURATED = [
    StoryParams(setting="ship", action="chowmein", prize="chowmein", name="Mira", role="pirate", captain="Capn Wren", trait="cheeky"),
    StoryParams(setting="ship", action="chowmein", prize="chowmein", name="Bram", role="pirate", captain="Captain Salt", trait="brisk"),
]


ASP_RULES = r"""
valid(S,A,P) :- setting(S), action(A), prize(P), affords(S,A), match(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("match", pid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with chowmein, rhyme, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["pirate"])
    ap.add_argument("--captain")
    ap.add_argument("--trait", choices=PIRATE_TRAITS)
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
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or "ship"
    action = getattr(args, "action", None) or "chowmein"
    prize = getattr(args, "prize", None) or "chowmein"
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    role = getattr(args, "role", None) or "pirate"
    captain = getattr(args, "captain", None) or rng.choice(["Captain Salt", "Capn Wren", "Old Hook"])
    trait = getattr(args, "trait", None) or rng.choice(PIRATE_TRAITS)
    return StoryParams(setting=setting, action=action, prize=prize, name=name, role=role, captain=captain, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
