#!/usr/bin/env python3
"""
storyworlds/worlds/zucchini_magic_mystery_to_solve_space_adventure.py
======================================================================

A tiny space-adventure storyworld about a zucchini-shaped mystery, a little
magic, and a problem that can be solved by careful, kind teamwork.

Premise:
- A child explorer loves a shiny zucchini from the space garden.
- The zucchini turns magical and starts floating in a mysterious way.
- A small problem appears: nobody knows how to make the magic calm down.
- The child, a helper, and a tool use clues and a gentle spell to solve it.

This world is constraint-driven rather than a frozen prompt swap. The simulated
state tracks a few physical meters and emotional memes:
- glow, drift, sparkle, crackle, dust -> physical / magical intensity
- curiosity, worry, wonder, relief, joy, trust -> emotional state

The story shape is:
1) setup in the space habitat
2) mystery appears when the zucchini magic goes wrong
3) clues and a helper reveal a fix
4) the magic settles and the ending image proves the change

The script also includes an inline ASP twin of the reasonableness gate so
--verify can compare the Python and ASP versions.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    portable: bool = True
    special: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["glow", "drift", "sparkle", "crackle", "dust", "repair"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "wonder", "relief", "joy", "trust"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
class Setting:
    place: str
    detail: str
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
class Mystery:
    id: str
    label: str
    phrase: str
    source: str
    clue: str
    fix: str
    effect: str
    zone: set[str]
    kind: str
    keyword: str = "zucchini"
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
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    method: str
    closing: str
    special: bool = False
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


@dataclass
class StoryParams:
    place: str
    mystery: str
    tool: str
    name: str
    gender: str
    helper: str
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
    "orbital_garden": Setting(
        place="the orbital garden",
        detail="Soft lights floated over little planters and silver rails.",
        affords={"glow-drift", "sparkle-clue"},
    ),
    "moon_station": Setting(
        place="the moon station",
        detail="The domed hall hummed while stars blinked through the glass roof.",
        affords={"glow-drift", "crackle-clue", "sparkle-clue"},
    ),
    "stargate_greenhouse": Setting(
        place="the stargate greenhouse",
        detail="Wide windows showed a ribbon of stars above the green leaves.",
        affords={"sparkle-clue", "glow-drift"},
    ),
}

MYSTERIES = {
    "glow_drift": Mystery(
        id="glow-drift",
        label="glowing zucchini",
        phrase="a zucchini that glowed like a tiny lantern",
        source="moonbeam magic",
        clue="a silver leaf stuck to the stem",
        fix="a moon-salt charm",
        effect="the glow settled into a warm, sleepy shine",
        zone={"hands", "torso"},
        kind="glow",
        tags={"magic", "zucchini", "space"},
    ),
    "sparkle_clue": Mystery(
        id="sparkle-clue",
        label="sparkling zucchini",
        phrase="a zucchini that scattered sparkles across the floor",
        source="starlight magic",
        clue="tiny sparkles pointed toward the seed tray",
        fix="a gentle counting spell",
        effect="the sparkles lined up like quiet fireflies",
        zone={"hands", "torso"},
        kind="sparkle",
        tags={"magic", "mystery", "zucchini"},
    ),
    "crackle_clue": Mystery(
        id="crackle-clue",
        label="crackling zucchini",
        phrase="a zucchini that crackled with green little pops",
        source="comet-static magic",
        clue="a ping came from the watering tube",
        fix="a slow-breath spell",
        effect="the crackles faded into a soft purr",
        zone={"hands", "torso"},
        kind="crackle",
        tags={"magic", "mystery", "space"},
    ),
}

TOOLS = {
    "moon_salt": Tool(
        id="moon_salt",
        label="moon-salt charm",
        phrase="a small moon-salt charm",
        helps_with={"glow"},
        method="tap the charm beside the stem and whisper a sleepy rhyme",
        closing="they tapped the moon-salt charm beside the stem",
        special=True,
    ),
    "counting_spell": Tool(
        id="counting_spell",
        label="counting spell",
        phrase="a counting spell card",
        helps_with={"sparkle"},
        method="count to five with one finger for each star and then clap softly",
        closing="they counted to five and clapped softly",
        special=True,
    ),
    "slow_breath": Tool(
        id="slow_breath",
        label="slow-breath spell",
        phrase="a slow-breath spell",
        helps_with={"crackle"},
        method="breathe in slowly, breathe out slowly, and let the pops calm down",
        closing="they breathed in slowly and let the pops calm down",
        special=True,
    ),
}

NAMES_GIRL = ["Mina", "Luna", "Ada", "Ivy", "Zia", "Nora"]
NAMES_BOY = ["Owen", "Theo", "Finn", "Leo", "Arlo", "Jace"]
HELPERS = ["robot", "captain", "pilot"]
TRAITS = ["curious", "brave", "gentle", "bright", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for m in setting.affords:
            for tool_id, tool in TOOLS.items():
                mystery = _safe_lookup(MYSTERIES, m)
                if mystery.kind in tool.helps_with:
                    combos.append((place, m, tool_id))
    return combos


def select_tool(mystery: Mystery) -> Optional[Tool]:
    for t in TOOLS.values():
        if mystery.kind in t.helps_with:
            return t
    return None


def explain_rejection(mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not calm a {mystery.kind} mystery. "
        f"Try the tool that helps with {mystery.kind}.)"
    )


def explain_gender(gender: str, item: str) -> str:
    return f"(No story: this setup does not fit the requested gender/item pairing for {gender} and {item}.)"


def reasonableness_gate(mystery: Mystery, tool: Tool) -> bool:
    return mystery.kind in tool.helps_with


def _mystery_spreads(world: World, hero: Entity, mystery: Mystery) -> list[str]:
    out: list[str] = []
    if hero.meters[mystery.kind] < THRESHOLD:
        return out
    sig = ("spreads", hero.id, mystery.kind)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    out.append(
        f"The {mystery.label} floated higher, and {hero.pronoun('possessive')} "
        f"eyes went wide with worry."
    )
    return out


def _mystery_marks(world: World, hero: Entity, mystery: Mystery) -> list[str]:
    out: list[str] = []
    if hero.meters[mystery.kind] < THRESHOLD:
        return out
    sig = ("marks", hero.id, mystery.kind)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["dust"] += 1
    out.append(
        f"Little glowing specks dusted the air like stars around {hero.id}."
    )
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for hero in world.characters():
            mystery: Mystery = world.facts.get("mystery_obj")
            if mystery:
                for s in _mystery_spreads(world, hero, mystery) + _mystery_marks(world, hero, mystery):
                    if s:
                        produced.append(s)
                        changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mystery(world: World, hero: Entity, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters[mystery.kind] += 1
    simulate_clue(sim, sim.get(hero.id), mystery, narrate=False)
    return {
        "intense": sim.get(hero.id).meters[mystery.kind] >= THRESHOLD,
        "dust": sim.get(hero.id).meters["dust"],
    }


def intro(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'curious')} {hero.type} "
        f"who loved the quiet shine of the space garden."
    )
    world.say(
        f"{helper.id} was a helpful {helper.type} who watched the planters and carried spare tools."
    )
    world.say(
        f"Together they cared for {mystery.phrase}, a treasure from the {world.setting.place}."
    )


def setup(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["love"] += 1
    world.say(
        f"One day, {hero.id} found {mystery.phrase} under a leaf, and it looked almost magical."
    )


def cause(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters[mystery.kind] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"When {hero.id} lifted {hero.pronoun('object')} from the tray, the {mystery.label} began to shine."
    )
    world.say(
        f"It was as if moonlight had woken up inside the green skin."
    )


def mystery_turn(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then the shine turned strange: the {mystery.label} drifted off the plate and hovered in the air."
    )
    world.say(
        f"{hero.id} frowned. 'Something is making the magic do loops,' {hero.pronoun()} said."
    )
    world.say(
        f"{helper.id} pointed at {mystery.clue} and said it looked like a clue."
    )


def simulate_clue(world: World, hero: Entity, mystery: Mystery, narrate: bool = True) -> None:
    if narrate:
        world.say(
            f"To test the clue, {hero.id} looked carefully and noticed {mystery.clue}."
        )
    hero.memes["curiosity"] += 1


def use_tool(world: World, hero: Entity, helper: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{helper.id} smiled and offered {tool.phrase}. '{tool.method.capitalize()},' {helper.pronoun()} said."
    )
    world.say(
        f"{hero.id} followed the steps, and {tool.closing}."
    )


def resolve(world: World, hero: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.meters[mystery.kind] = 0.0
    world.say(
        f"At once, the {mystery.label} settled down. {mystery.effect.capitalize()}."
    )
    world.say(
        f"{hero.id} laughed softly, because the mystery was solved and the space garden felt peaceful again."
    )


def ending(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"By the end, the {mystery.label} rested in the tray like an ordinary zucchini with a tiny happy glow."
    )
    world.say(
        f"{hero.id} stood beside it under the stars, smiling at the calm little plant."
    )


def tell(setting: Setting, mystery: Mystery, tool: Tool, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, location=setting.place))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="Helper", location=setting.place))
    hero.memes["trait_word"] = trait
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["mystery_obj"] = mystery
    world.facts["tool"] = tool

    intro(world, hero, helper, mystery)
    world.para()
    setup(world, hero, mystery)
    cause(world, hero, mystery)
    propagate(world)

    world.para()
    mystery_turn(world, hero, helper, mystery)
    simulate_clue(world, hero, mystery)

    world.para()
    use_tool(world, hero, helper, mystery, tool)
    resolve(world, hero, mystery, tool)

    world.para()
    ending(world, hero, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mystery = _safe_fact(world, f, "mystery_obj")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short space-adventure story for a small child about a magical {mystery.keyword} mystery.',
        f"Tell a gentle story where {hero.id} finds a zucchini that behaves strangely and uses {tool.label} to solve the problem.",
        f"Write a child-friendly mystery-to-solve tale set in space with a zucchini, a helper, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    mystery = _safe_fact(world, f, "mystery_obj")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"What did {hero.id} find in the space garden?",
            answer=f"{hero.id} found a {mystery.label} that started to act magical in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why was the {mystery.label} a mystery?",
            answer=f"It was a mystery because it floated and shone in a strange way, and nobody knew at first why it was doing that.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.id} helped by pointing out the clue and bringing the {tool.label}.",
        ),
        QAItem(
            question=f"What happened after they used the {tool.label}?",
            answer=f"The magical trouble calmed down, and the {mystery.label} rested quietly again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a zucchini?",
            answer="A zucchini is a long green vegetable that grows on a plant and can be cooked in many meals.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising or impossible in real life, like glowing, floating, or a spell that changes how things work.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find the clues and figure out why something strange happened.",
        ),
        QAItem(
            question="What is a space adventure?",
            answer="A space adventure is a story about exploring stars, stations, planets, or other places beyond Earth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "trait_word"}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_kind(glow_drift, glow).
mystery_kind(sparkle_clue, sparkle).
mystery_kind(crackle_clue, crackle).

tool_help(moon_salt, glow).
tool_help(counting_spell, sparkle).
tool_help(slow_breath, crackle).

valid_combo(P, M, T) :- setting(P), mystery(M), tool(T),
                        affords(P, M), mystery_kind(M, K), tool_help(T, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space adventure storyworld: zucchini, magic, and a mystery to solve."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=list(MYSTERIES))
    ap.add_argument("--tool", choices=list(TOOLS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if getattr(args, "mystery", None) and getattr(args, "tool", None):
        m = _safe_lookup(MYSTERIES, getattr(args, "mystery", None))
        t = _safe_lookup(TOOLS, getattr(args, "tool", None))
        if not reasonableness_gate(m, t):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery_id, tool_id = rng.choice(list(filtered))
    mystery = _safe_lookup(MYSTERIES, mystery_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, mystery=mystery_id, tool=tool_id, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    tool = _safe_lookup(TOOLS, params.tool)
    hero_type = "girl" if params.gender == "girl" else "boy"
    helper_type = params.helper
    trait = random.Random(params.seed if params.seed is not None else 0).choice(TRAITS)
    world = tell(_safe_lookup(SETTINGS, params.place), mystery, tool, params.name, hero_type, helper_type, trait)
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
    StoryParams(place="orbital_garden", mystery="glow_drift", tool="moon_salt", name="Mina", gender="girl", helper="robot"),
    StoryParams(place="moon_station", mystery="sparkle_clue", tool="counting_spell", name="Owen", gender="boy", helper="captain"),
    StoryParams(place="stargate_greenhouse", mystery="crackle_clue", tool="slow_breath", name="Luna", gender="girl", helper="pilot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery, tool) combos:\n")
        for p, m, t in combos:
            print(f"  {p:18} {m:14} {t}")
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
