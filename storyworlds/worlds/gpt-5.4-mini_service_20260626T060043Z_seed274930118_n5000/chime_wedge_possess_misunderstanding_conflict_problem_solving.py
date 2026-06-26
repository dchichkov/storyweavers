#!/usr/bin/env python3
"""
A standalone story world for a tiny detective-style mystery.

Premise:
A child detective tries to solve a small misunderstanding about a missing
chime. A wooden wedge, a locked drawer, and a suspicious note create conflict.
The turn comes when the detective uses patient problem solving to show that
"possess" meant "is keeping safely," not "has stolen." The ending image proves
the chime is back where it belongs.

This file follows the Storyweavers world contract:
- self-contained stdlib script
- eager import of shared results containers
- lazy import of storyworlds/asp in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    detective: object | None = None
    suspect_ent: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    indoors: bool = True
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
class Clue:
    id: str
    label: str
    phrase: str
    signal: str
    hidden_in: str
    move_with: str
    meaning: str
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps_with: str
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
class SuspectProfile:
    id: str
    name: str
    type: str
    role: str
    relation: str
    likely_action: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def _indefinite(phrase: str) -> str:
    first = phrase.strip().lower()[:1]
    return ("an " if first in "aeiou" else "a ") + phrase


def _capitalize_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _possess_phrase(owner: str, noun: str) -> str:
    return f"{owner}'s {noun}"


def _pronoun_name(hero: Entity) -> str:
    return hero.id


def _do_detective_move(world: World, hero: Entity, tool: Tool, clue: Clue) -> None:
    hero.meters["attention"] = hero.meters.get("attention", 0.0) + 1.0
    if tool.helps_with == clue.hidden_in:
        clue.meters["found"] = 1.0
        world.say(f"{hero.id} used {tool.phrase} and found the clue tucked inside the {clue.hidden_in}.")


def _maybe_misunderstanding(world: World) -> None:
    if world.facts.get("misunderstanding"):
        world.say("But the room still felt uneasy, because the first clue sounded like blame.")


def _apply_conflict(world: World, hero: Entity, suspect: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    suspect.memes["fear"] = suspect.memes.get("fear", 0.0) + 1.0


def _apply_resolution(world: World, hero: Entity, suspect: Entity, clue: Clue) -> None:
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    suspect.memes["fear"] = 0.0
    clue.meters["shown"] = 1.0


def detect_turn(world: World, hero: Entity, suspect: Entity, clue: Clue, tool: Tool) -> None:
    if clue.meters.get("found", 0.0) < THRESHOLD:
        return
    if world.facts.get("misunderstanding"):
        world.say(
            f"{hero.id} read the note again and smiled. It did not mean that {suspect.id} had stolen anything; "
            f"it meant {suspect.pronoun('subject')} was trying to possess the broken chime safely."
        )
    else:
        world.say(f"{hero.id} realized the clue pointed straight to the drawer, not to {suspect.id}.")
    _apply_resolution(world, hero, suspect, clue)
    world.say(
        f"So {hero.id} used {tool.phrase} to open the drawer, and the little chime sat inside, "
        f"safe and shiny, as if it had been waiting for the whole case to end."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, suspect: SuspectProfile, clue: Clue, tool: Tool) -> World:
    world = World(setting)
    detective = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="detective"))
    suspect_ent = world.add(Entity(id=suspect.id, kind="character", type=suspect.type, label=suspect.role))
    clue_ent = world.add(Entity(id=clue.id, type="thing", label=clue.label, phrase=clue.phrase))
    tool_ent = world.add(Entity(id=tool.id, type="thing", label=tool.label, phrase=tool.phrase))

    world.facts["misunderstanding"] = True

    world.say(
        f"At {setting.place}, {detective.id} was a small detective who loved careful clues and quiet rooms."
    )
    world.say(
        f"One morning, {detective.id} found a note near the shelf: {_indefinite(clue.phrase)} had been moved, "
        f"and somebody seemed to possess the only key."
    )
    world.say(
        f"{detective.id} frowned, because the note sounded suspicious. It made {suspect_ent.id} seem guilty before anyone asked why."
    )

    world.para()
    world.say(
        f"{suspect_ent.id} stood by the drawer looking worried. {suspect_ent.pronoun('subject').capitalize()} said, "
        f'\"I only meant to possess it until it was fixed.\"'
    )
    world.say(
        f"But {detective.id} misunderstood the word possess and thought {suspect_ent.id} meant to keep the chime forever."
    )
    _apply_conflict(world, detective, suspect_ent)
    world.say(
        f"That misunderstanding turned the room tense. {detective.id} crossed {detective.pronoun('possessive')} arms and kept staring at the drawer."
    )

    world.para()
    world.say(
        f"Then {detective.id} noticed a narrow gap in the old drawer. The gap was just wide enough for {tool_ent.phrase}."
    )
    _do_detective_move(world, detective, tool_ent, clue_ent)
    _maybe_misunderstanding(world)
    detect_turn(world, detective, suspect_ent, clue_ent, tool_ent)

    world.facts.update(
        detective=detective,
        suspect=suspect_ent,
        clue=clue_ent,
        tool=tool_ent,
        setting=setting,
        suspect_profile=suspect,
        clue_profile=clue,
        tool_profile=tool,
        resolved=True,
    )
    return world


SETTINGS = {
    "hallway": Setting(place="the hallway", indoors=True),
    "library": Setting(place="the little library", indoors=True),
    "workshop": Setting(place="the workshop", indoors=True),
    "porch": Setting(place="the porch", indoors=False),
}

CLUES = {
    "chime": Clue(
        id="chime",
        label="chime",
        phrase="a tiny brass chime",
        signal="soft ringing",
        hidden_in="drawer",
        move_with="note",
        meaning="a broken bell kept safe for repair",
    ),
    "wedge": Clue(
        id="wedge",
        label="wedge",
        phrase="a wooden wedge",
        signal="thin tap",
        hidden_in="doorframe",
        move_with="note",
        meaning="a tool for holding something open",
    ),
}

TOOLS = {
    "wedge": Tool(
        id="wedge",
        label="wedge",
        phrase="the wooden wedge",
        use="pry open a stuck drawer",
        helps_with="drawer",
    ),
    "key": Tool(
        id="key",
        label="key",
        phrase="the small brass key",
        use="unlock a box",
        helps_with="box",
    ),
}

SUSPECTS = {
    "caretaker": SuspectProfile(
        id="Mira",
        name="Mira",
        type="woman",
        role="caretaker",
        relation="neighbor",
        likely_action="kept the chime safe for repair",
    ),
    "brother": SuspectProfile(
        id="Noah",
        name="Noah",
        type="boy",
        role="brother",
        relation="brother",
        likely_action="borrowed the wedge to hold the door open",
    ),
    "shopkeeper": SuspectProfile(
        id="Ivy",
        name="Ivy",
        type="woman",
        role="shopkeeper",
        relation="shopkeeper",
        likely_action="kept the chime behind the counter",
    ),
}

GIRL_NAMES = ["Ada", "Mina", "Lina", "Rae", "Mila"]
BOY_NAMES = ["Eli", "Owen", "Finn", "Leo", "Ben"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    tool: str
    suspect: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for clue in CLUES:
            for tool in TOOLS:
                for suspect in SUSPECTS:
                    if clue == "chime" and tool == "wedge":
                        combos.append((setting, clue, tool, suspect))
    return combos


KNOWLEDGE = {
    "chime": [(
        "What is a chime?",
        "A chime is a small bell or metal piece that makes a light ringing sound when it moves or is tapped."
    )],
    "wedge": [(
        "What is a wedge used for?",
        "A wedge is a tool or shaped piece that can fit into a narrow space to hold things apart or open them."
    )],
    "possess": [(
        "What does possess mean?",
        "To possess something means to have it, keep it, or own it."
    )],
    "detective": [(
        "What does a detective do?",
        "A detective looks for clues, asks careful questions, and tries to solve a problem."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child about {f["detective"].id}, a missing {f["clue"].label}, and a {(f.get("tool") or next(iter(TOOLS.values()))).label}.',
        f'Write a mystery story where the word "possess" causes a misunderstanding, and the detective solves it with patient clue-finding.',
        f'Write a gentle conflict-and-resolution story set at {f["setting"].place} that includes a chime and a wedge.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = _safe_fact(world, f, "detective")
    sus = _safe_fact(world, f, "suspect")
    clue = _safe_fact(world, f, "clue")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is solving the mystery at {setting.place}?",
            answer=f"{det.id} is the small detective who solves the mystery at {setting.place}.",
        ),
        QAItem(
            question=f"What confused {det.id} at first about {sus.id} and the word possess?",
            answer=(
                f"{det.id} thought {sus.id} meant to keep the {clue.label} forever, but the word possess only meant "
                f"to keep it safely for a while."
            ),
        ),
        QAItem(
            question=f"What tool helped open the drawer and show where the {clue.label} was hiding?",
            answer=(
                f"The {tool.label} helped open the drawer, and that let {det.id} find the {clue.label} in the end."
            ),
        ),
        QAItem(
            question=f"What changed after the misunderstanding was solved?",
            answer=(
                f"The conflict went away, {sus.id} stopped looking worried, and the {clue.label} was back where it belonged."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    tags = {f["clue"].id, (f.get("tool") or next(iter(TOOLS.values()))).id, "detective", "possess"}
    for tag in ["chime", "wedge", "possess", "detective"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="library", clue="chime", tool="wedge", suspect="caretaker", name="Ada", gender="girl"),
    StoryParams(setting="hallway", clue="chime", tool="wedge", suspect="brother", name="Eli", gender="boy"),
    StoryParams(setting="workshop", clue="chime", tool="wedge", suspect="shopkeeper", name="Mina", gender="girl"),
]


ASP_RULES = r"""
% A clue is at risk when it can be hidden in the chosen place.
at_risk(chime, Place) :- setting(Place), indoors(Place).
at_risk(chime, Place) :- setting(Place), outdoors(Place).

% A wedge is the compatible tool for a stuck drawer mystery.
good_tool(wedge, chime).

% A valid detective story needs an at-risk clue, a useful tool, and a suspect.
valid_story(Place, Clue, Tool, Suspect) :-
    setting(Place), clue(Clue), tool(Tool), suspect(Suspect),
    at_risk(Clue, Place), good_tool(Tool, Clue).

#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        else:
            lines.append(asp.fact("outdoors", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    py_set = set((s, "chime", "wedge", p) for s, _, _, p in valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world about a chime, a wedge, and a possessive misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "clue", None):
        combos = [c for c in combos if c[1] == getattr(args, "clue", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if getattr(args, "suspect", None):
        combos = [c for c in combos if c[3] == getattr(args, "suspect", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, clue, tool, suspect = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, clue=clue, tool=tool, suspect=suspect, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params.name, "girl" if params.gender == "girl" else "boy",
                 _safe_lookup(SUSPECTS, params.suspect), _safe_lookup(CLUES, params.clue), _safe_lookup(TOOLS, params.tool))
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, clue, tool, suspect in stories:
            print(f"  {place:10} {clue:8} {tool:8} {suspect}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
